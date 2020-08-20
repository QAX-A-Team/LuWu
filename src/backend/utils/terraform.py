import base64
import contextlib
import logging
import time
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from typing import List

from python_terraform import IsFlagged
from python_terraform import Terraform as TF
from terrascript import Data
from terrascript import Output
from terrascript import Provider
from terrascript import Resource
from terrascript import Terrascript
from terrascript import provider
from terrascript import provisioner
from terrascript import resource
from terrascript import terraform

from core.config import PROJECT_NAME
from core.config import TERRAFORM_WORK_DIR
from utils.template import TemplateRender


class Terraform:
    DEFAULT_DOCKER_HOST = "unix:///var/run/docker.sock"
    DEFAULT_DOCKER_ENTRYPOINT_PATH = "/docker-entrypoint.sh"
    DEFAULT_NGINX_DOCKER_ENTRYPOINT_PATH = "/nginx.docker-entrypoint.sh"
    DEFAULT_NGINX_DOCKER_IMAGE = "nginx:stable-alpine"
    DEFAULT_NGINX_DOCKER_CONTAINER_HTML_PATH = "/usr/share/nginx/html"
    DEFAULT_UPLOAD_PATH = f"$HOME/.{PROJECT_NAME}/"
    DEFAULT_SSH_USER = "root"
    DEFAULT_SSH_PORT = 22

    TERRAFORM_RESOURCE_FILE = "file"

    # trick for terrascript
    class null_resource(Resource):
        ...

    class tencentcloud(Provider):
        ...

    class tencentcloud_availability_zones(Data):
        ...

    class tencentcloud_images(Data):
        ...

    class tencentcloud_instance_types(Data):
        ...

    class tencentcloud_security_group(Resource):
        ...

    class tencentcloud_security_group_lite_rule(Resource):
        ...

    class tencentcloud_instance(Resource):
        ...

    class tencentcloud_key_pair(Resource):
        ...

    class alicloud(Provider):
        ...

    class alicloud_vpc(Resource):
        ...

    class alicloud_key_pair(Resource):
        ...

    class alicloud_security_group(Resource):
        ...

    class alicloud_security_group_rule(Resource):
        ...

    class alicloud_instance(Resource):
        ...

    class alicloud_vswitch(Resource):
        ...

    class alicloud_zones(Data):
        ...

    class vultr(Provider):
        ...

    class vultr_server(Resource):
        ...

    class vultr_ssh_key(Resource):
        ...

    def __init__(self):
        self.work_dir = TERRAFORM_WORK_DIR
        self.app = TF(working_dir=self.work_dir)

    @contextlib.contextmanager
    def terraform_workspace(self):
        workspace = f"terraform_workspace_{int(time.time())}"
        self.app.create_workspace(workspace)
        tmp_dir = TemporaryDirectory()

        yield tmp_dir.name
        self.app.set_workspace("default")
        self.app.cmd("workspace delete", workspace, force=IsFlagged)

    @contextlib.contextmanager
    def patch_terraform_docker_ssh_conn(self):
        # patch ssh config
        yield
        # clear ssh config

    def write_terraform_config(self, config: Terrascript, dir_path: str):
        tmp_config_file = NamedTemporaryFile(
            mode="wt", suffix=".tf.json", dir=dir_path, delete=False
        )
        logging.info(str(config))
        tmp_config_file.write(str(config))
        tmp_config_file.seek(0)

        self.app.init(
            dir_path
            # disable maual plugin because it changes toooo fast
            # dir_path, plugin_dir=f"{self.work_dir}/plugins",
        )

        return tmp_config_file

    def run_terraform_plan(self, config: Terrascript):
        with self.terraform_workspace() as tw_dir:
            self.write_terraform_config(config, tw_dir)
            plan = self.app.plan(tw_dir, no_color=IsFlagged)
        return plan

    def run_terraform_apply(self, config: Terrascript):
        with self.terraform_workspace() as tw_dir:
            self.write_terraform_config(config, tw_dir)

            self.app.apply(tw_dir, skip_plan=True, no_color=IsFlagged)
            output_result = self.app.output(json=IsFlagged, no_color=IsFlagged)

            output_var = {
                output_var_key: output_result[output_var_key]["value"]
                for output_var_key in output_result
            }

        return output_var

    def run_terraform_destroy(self, config: Terrascript):
        with self.terraform_workspace() as tw_dir:
            self.write_terraform_config(config, tw_dir)
            destroy_result = self.app.destroy(tw_dir)
        return destroy_result

    @classmethod
    def gen_digital_ocean_config(
        cls, config_data: dict, token: str, public_key: str = None
    ):
        do_config = Terrascript()
        do_provider = provider.digitalocean(token=token)
        do_droplet_resource = resource.digitalocean_droplet(
            "server",
            image=config_data["os_code"],
            name=config_data["hostname"],
            region=config_data["region_code"],
            size=config_data["plan_code"],
            ssh_keys=config_data["ssh_keys"] if config_data.get("ssh_keys") else [],
        )
        if public_key:
            digitalocean_ssh_key = resource.digitalocean_ssh_key(
                "digitalocean_ssh_key", name="default", public_key=public_key,
            )

            do_droplet_resource["ssh_keys"] += [
                "${digitalocean_ssh_key.digitalocean_ssh_key.id}"
            ]
            do_config += digitalocean_ssh_key

        do_output_ip = Output("ip", value="${digitalocean_droplet.server.ipv4_address}")
        do_output_id = Output("server_id", value="${digitalocean_droplet.server.id}")
        do_config += do_provider
        do_config += do_droplet_resource
        do_config += do_output_ip
        do_config += do_output_id

        return do_config

    @classmethod
    def gen_vultr_config(cls, config_data: dict, token: str, public_key: str = None):
        vultr_config = Terrascript()
        vultr_provider = cls.vultr(api_key=token, rate_limit=700, retry_limit=3)

        vultr_server = cls.vultr_server(
            "server",
            plan_id=config_data["plan_code"],
            region_id=config_data["region_code"],
            os_id=config_data["os_code"],
            hostname=config_data["hostname"],
            ssh_key_ids=config_data["ssh_keys"] if config_data.get("ssh_keys") else [],
        )
        vultr_output_ip = Output("ip", value="${vultr_server.server.main_ip}")
        vultr_output_id = Output("server_id", value="${vultr_server.server.id}")

        if public_key:
            vultr_ssh_key = cls.vultr_ssh_key(
                "vultr_ssh_key", name="default_key", ssh_key=public_key
            )

            vultr_server["ssh_key_ids"] += ["${vultr_ssh_key.vultr_ssh_key.id}"]
            vultr_config += vultr_ssh_key

        vultr_config += vultr_provider
        vultr_config += vultr_server
        vultr_config += vultr_output_ip
        vultr_config += vultr_output_id

        return vultr_config

    @classmethod
    def gen_tencent_cloud_config(
        cls,
        config_data: dict,
        token: str,
        public_key_name: str = None,
        secret_id: str = None,
    ):
        tencent_cloud_config = Terrascript()
        tencent_terraform = terraform(
            **{
                "required_providers": {
                    "tencentcloud": {
                        "source": "terraform-providers/tencentcloud",
                        "version": "~> 1.40.3",
                    },
                }
            }
        )

        tencent_cloud_provider = cls.tencentcloud(
            secret_id=secret_id, secret_key=token, region=config_data["region_code"],
        )
        tencent_zone = cls.tencentcloud_availability_zones("default")
        tencent_security_group = cls.tencentcloud_security_group(
            "default", name="all-open", description="open all ports"
        )
        tencent_security_group_rule = cls.tencentcloud_security_group_lite_rule(
            "rule",
            security_group_id="${tencentcloud_security_group.default.id}",
            ingress=[
                "ACCEPT#10.0.0.0/8#ALL#ALL",
            ],
            egress=[
                "ACCEPT#10.0.0.0/8#ALL#ALL",
            ],
        )
        tencent_cloud_server = cls.tencentcloud_instance(
            "server",
            instance_name=config_data["hostname"],
            availability_zone="${data.tencentcloud_availability_zones.default.zones.0.name}",
            image_id=config_data["os_code"],
            instance_type=config_data["plan_code"],
            disable_monitor_service=True,
            disable_security_service=True,
            allocate_public_ip=True,
            internet_max_bandwidth_out=5,
            instance_charge_type="POSTPAID_BY_HOUR",
            internet_charge_type="TRAFFIC_POSTPAID_BY_HOUR",
            system_disk_type="CLOUD_SSD",
            count=1,
        )
        tencent_output_ip = Output(
            "ip", value="${tencentcloud_instance.server.0.public_ip}"
        )
        tencent_output_id = Output(
            "server_id", value="${tencentcloud_instance.server.0.id}"
        )

        if public_key_name:
            tencent_cloud_server["key_name"] = public_key_name

        tencent_cloud_config += tencent_terraform
        tencent_cloud_config += tencent_cloud_provider
        tencent_cloud_config += tencent_zone
        tencent_cloud_config += tencent_security_group
        tencent_cloud_config += tencent_security_group_rule
        tencent_cloud_config += tencent_cloud_server
        tencent_cloud_config += tencent_output_ip
        tencent_cloud_config += tencent_output_id

        return tencent_cloud_config

    @classmethod
    def gen_ali_cloud_config(
        cls,
        config_data: dict,
        token: str,
        ssh_key_name: str = None,
        access_key: str = None,
        security_groups: List[str] = [],
    ):
        ali_cloud_config = Terrascript()
        ali_cloud_provider = cls.alicloud(
            access_key=access_key, secret_key=token, region=config_data["region_code"],
        )

        ali_zone = cls.alicloud_zones(
            "default",
            available_disk_category="cloud_efficiency",
            available_resource_creation="Instance",
        )
        ali_vpc = cls.alicloud_vpc("vpc", cidr_block="172.16.0.0/12",)
        ali_vswitch = cls.alicloud_vswitch(
            "vswitch",
            vpc_id="${alicloud_vpc.vpc.id}",
            cidr_block="172.16.0.0/29",
            availability_zone="${data.alicloud_zones.default.zones.0.id}",
        )
        ali_security_group = cls.alicloud_security_group(
            "group",
            name="all-open",
            vpc_id="${alicloud_vpc.vpc.id}",
            description="open all ports",
            inner_access_policy="Accept",
        )
        ali_internet_security_group_rule = cls.alicloud_security_group_rule(
            "internet",
            # nic_type="internet",
            security_group_id="${alicloud_security_group.group.id}",
            type="ingress",
            port_range="-1/-1",
            cidr_ip="0.0.0.0/0",
            ip_protocol="all",
            policy="accept",
        )
        ali_intranet_security_group_rule = cls.alicloud_security_group_rule(
            "intranet",
            # nic_type="intranet",
            security_group_id="${alicloud_security_group.group.id}",
            port_range="-1/-1",
            type="egress",
            cidr_ip="0.0.0.0/0",
            ip_protocol="all",
            policy="accept",
            priority=1,
        )
        ali_cloud_server = cls.alicloud_instance(
            "server",
            instance_name=config_data["hostname"],
            availability_zone="${data.alicloud_zones.default.zones.0.id}",
            # security_groups=security_groups,
            security_groups="${alicloud_security_group.group.*.id}",
            vswitch_id="${alicloud_vswitch.vswitch.id}",
            image_id=config_data["os_code"],
            instance_type=config_data["plan_code"],
            security_enhancement_strategy="Deactive",
            instance_charge_type="PostPaid",
            internet_charge_type="PayByTraffic",
            internet_max_bandwidth_out=2,
        )
        ali_output_ip = Output("ip", value="${alicloud_instance.server.public_ip}")
        ali_output_id = Output("server_id", value="${alicloud_instance.server.id}")

        if ssh_key_name:
            ali_cloud_server["key_name"] = ssh_key_name

        ali_cloud_config += ali_cloud_provider
        ali_cloud_config += ali_zone
        ali_cloud_config += ali_vpc
        ali_cloud_config += ali_vswitch
        ali_cloud_config += ali_security_group
        ali_cloud_config += ali_internet_security_group_rule
        ali_cloud_config += ali_intranet_security_group_rule
        ali_cloud_config += ali_cloud_server
        ali_cloud_config += ali_output_ip
        ali_cloud_config += ali_output_id

        return ali_cloud_config

    @classmethod
    def add_ssh_key_config(cls, public_key: str):
        return provisioner(
            "remote-exec",
            provisioner=provisioner(
                "remote-exec",
                inline=["mkdir -p ~/.ssh", f"{public_key} >> ~/.ssh/authorized_keys"],
            ),
        )

    @classmethod
    def gen_ssh_conn_config(
        cls,
        *,
        ssh_user: str = DEFAULT_SSH_USER,
        ssh_private_key: str,
        ssh_host: str,
        ssh_port: int = DEFAULT_SSH_PORT,
    ) -> dict:

        # see more in https://www.terraform.io/docs/provisioners/connection.html
        return {
            "type": "ssh",
            "user": ssh_user,
            "private_key": ssh_private_key,
            "host": ssh_host,
            "port": ssh_port,
            "timeout": "30s",
        }

    @classmethod
    def gen_site_docker_deploy_config(
        cls,
        *,
        docker_host: str = DEFAULT_DOCKER_HOST,
        site_name: str = None,
        template_tar_bytes: bytes = None,
        script: str = None,
        ssh_user: str = DEFAULT_SSH_USER,
        ssh_private_key: str,
        ssh_host: str,
        ssh_port: int = DEFAULT_SSH_PORT,
    ):
        config = Terrascript()
        docker_provider = provider.docker(
            host=docker_host,
            connection=cls.gen_ssh_conn_config(
                ssh_user=ssh_user,
                ssh_private_key=ssh_private_key,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
            ),
        )
        docker_image_resource = resource.docker_image(
            "nginx_image", name=cls.DEFAULT_NGINX_DOCKER_IMAGE,
        )
        docker_container_resource = resource.docker_container(
            "nginx_container",
            name=f"{site_name}-container-${{random_pet.docker_pet_name.id}}",
            image="${docker_image.nginx_image.latest}",
            restart="always",
            start=True,
            ports={"internal": 80},
            upload=[],
        )
        docker_name_resource = resource.random_pet("docker_pet_name", length=1,)

        if template_tar_bytes:
            template_tar_file = (
                f"{site_name}-tar-${{random_pet.docker_pet_name.id}}.tar.gz",
            )
            template_tar_file_content = base64.b64encode(template_tar_bytes).decode(
                "utf8"
            )
            template_tar_path = (
                f"{cls.DEFAULT_NGINX_DOCKER_CONTAINER_HTML_PATH}/${template_tar_file}"
            )
            # self.upload_file(
            #     content='conf/myapp.conf',
            #     destination=f"{self.DEFAULT_UPLOAD_PATH}/${template_tar_file}",
            #     ssh_user=ssh_user,
            #     ssh_private_key=ssh_private_key,
            #     ssh_host=ssh_host,
            #     ssh_port=ssh_port
            # )
            docker_container_resource["upload"].append(
                {"content_base64": template_tar_file_content, "file": template_tar_path}
            )

        if script:
            entrypoint_sh_content = TemplateRender().render(
                cls.DEFAULT_NGINX_DOCKER_ENTRYPOINT_PATH,
                init_script_path=cls.DEFAULT_DOCKER_ENTRYPOINT_PATH,
                html_path=cls.DEFAULT_NGINX_DOCKER_CONTAINER_HTML_PATH,
            )
            docker_container_resource["upload"].append(
                {
                    "content": entrypoint_sh_content,
                    "file": cls.DEFAULT_DOCKER_ENTRYPOINT_PATH,
                }
            )

        config += docker_provider
        config += docker_image_resource
        config += docker_container_resource
        config += docker_name_resource

        return config

    def remote_exec(
        self,
        *,
        ssh_user: str = DEFAULT_SSH_USER,
        ssh_private_key: str,
        ssh_host: str,
        ssh_port: int = DEFAULT_SSH_PORT,
    ):
        exec_config = Terrascript()
        ssh_conn = self.gen_ssh_conn_config(
            ssh_user=ssh_user,
            ssh_private_key=ssh_private_key,
            ssh_host=ssh_host,
            ssh_port=ssh_port,
        )
        exec_resource = self.null_resource(
            "remote-exec",
            provisioner=provisioner(
                "remote-exec", inline=["ls -la"], connection=ssh_conn
            ),
        )

        exec_config += exec_resource
        return exec_config

    def upload_file(
        self,
        content: str,
        *,
        destination: str = DEFAULT_UPLOAD_PATH,
        ssh_user: str = DEFAULT_SSH_USER,
        ssh_private_key: str,
        ssh_host: str,
        ssh_port: int = DEFAULT_SSH_PORT,
    ):
        upload_config = Terrascript()

        ssh_conn = self.gen_ssh_conn_config(
            ssh_user=ssh_user,
            ssh_private_key=ssh_private_key,
            ssh_host=ssh_host,
            ssh_port=ssh_port,
        )
        file_resource = self.null_resource(
            "upload_file_resource",
            provisioner=provisioner(
                self.TERRAFORM_RESOURCE_FILE,
                content=content,
                destination=destination,
                connection=ssh_conn,
            ),
        )

        upload_config += file_resource
        return upload_config
