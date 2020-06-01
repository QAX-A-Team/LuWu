import base64
import contextlib
import time
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory

from python_terraform import IsFlagged
from python_terraform import Terraform as TF
from terrascript import Output
from terrascript import Provider
from terrascript import Resource
from terrascript import Terrascript
from terrascript import provider
from terrascript import provisioner
from terrascript import resource

from app.core.config import PROJECT_NAME
from app.core.config import TERRAFORM_WORK_DIR
from utils.template import TemplateRender


class Terraform:
    DEFAULT_DOCKER_HOST = 'unix:///var/run/docker.sock'
    DEFAULT_DOCKER_ENTRYPOINT_PATH = '/docker-entrypoint.sh'
    DEFAULT_NGINX_DOCKER_ENTRYPOINT_PATH = '/nginx.docker-entrypoint.sh'
    DEFAULT_NGINX_DOCKER_IMAGE = 'nginx:stable-alpine'
    DEFAULT_NGINX_DOCKER_CONTAINER_HTML_PATH = '/usr/share/nginx/html'
    DEFAULT_UPLOAD_PATH = f"$HOME/.{PROJECT_NAME}/"
    DEFAULT_SSH_USER = 'root'
    DEFAULT_SSH_PORT = 22

    TERRAFORM_RESOURCE_FILE = 'file'

    # trick for terrascript
    class null_resource(Resource):
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
        self.app.set_workspace('default')
        self.app.cmd('workspace delete', workspace, force=IsFlagged)

    @contextlib.contextmanager
    def patch_terraform_docker_ssh_conn(self):
        # patch ssh config
        yield
        # clear ssh config

    def write_terraform_config(self, config: Terrascript, dir_path: str):
        tmp_config_file = NamedTemporaryFile(mode='wt', suffix='.tf.json', dir=dir_path, delete=False)
        tmp_config_file.write(str(config))
        tmp_config_file.seek(0)

        self.app.init(dir_path, plugin_dir=f"{self.work_dir}/plugins", )

        return tmp_config_file

    def run_terraform_plan(self, config: Terrascript):
        with self.terraform_workspace() as tw_dir:
            self.write_terraform_config(config, tw_dir)
            plan = self.app.plan(tw_dir, no_color=IsFlagged)
        return plan

    def run_terraform_apply(self, config: Terrascript):
        with self.terraform_workspace() as tw_dir:
            self.write_terraform_config(config, tw_dir)
            print(config)
            self.app.apply(tw_dir, skip_plan=True, no_color=IsFlagged)
            output_result = self.app.output(json=IsFlagged, no_color=IsFlagged)
            print(output_result)
            output_var = {
                output_var_key: output_result[output_var_key]['value']
                for output_var_key in output_result
            }

        return output_var

    def run_terraform_destroy(self, config: Terrascript):
        with self.terraform_workspace() as tw_dir:
            self.write_terraform_config(config, tw_dir)
            destroy_result = self.app.destroy(tw_dir)
        return destroy_result

    @classmethod
    def gen_digital_ocean_config(cls, config_data: dict, token: str, public_key: str = None):
        do_config = Terrascript()
        do_provider = provider.digitalocean(
            token=token
        )
        do_droplet_resource = resource.digitalocean_droplet(
            f"server",
            image=config_data['os_code'],
            name=config_data['hostname'],
            region=config_data['region_code'],
            size=config_data['plan_code'],
            ssh_keys=config_data['ssh_keys'] if config_data.get('ssh_keys') else []
        )
        if public_key:
            digitalocean_ssh_key = resource.digitalocean_ssh_key(
                "digitalocean_ssh_key",
                name="default",
                public_key=public_key,
            )

            do_droplet_resource['ssh_keys'] += ["${digitalocean_ssh_key.digitalocean_ssh_key.id}"]
            do_config += digitalocean_ssh_key

        do_output_ip = Output(
            'ip',
            value="${digitalocean_droplet.server.ipv4_address}"
        )
        do_output_id = Output(
            'server_id',
            value="${digitalocean_droplet.server.id}"
        )
        do_config += do_provider
        do_config += do_droplet_resource
        do_config += do_output_ip
        do_config += do_output_id

        return do_config

    @classmethod
    def gen_vultr_config(cls, config_data: dict, token: str, public_key: str = None):
        vultr_config = Terrascript()
        vultr_provider = cls.vultr(
            api_key=token,
            rate_limit=700,
            retry_limit=3
        )

        vultr_server = cls.vultr_server(
            f"server",
            plan_id=config_data['plan_code'],
            region_id=config_data['region_code'],
            os_id=config_data['os_code'],
            hostname=config_data['hostname'],
            ssh_key_ids=config_data['ssh_keys'] if config_data.get('ssh_keys') else []
        )
        vultr_output_ip = Output(
            'ip',
            value="${vultr_server.server.main_ip}"
        )
        vultr_output_id = Output(
            'server_id',
            value="${vultr_server.server.id}"
        )

        if public_key:
            vultr_ssh_key = cls.vultr_ssh_key(
                'vultr_ssh_key',
                name='default_key',
                ssh_key=public_key
            )

            vultr_server["ssh_key_ids"] += ["${vultr_ssh_key.vultr_ssh_key.id}"]
            vultr_config += vultr_ssh_key

        vultr_config += vultr_provider
        vultr_config += vultr_server
        vultr_config += vultr_output_ip
        vultr_config += vultr_output_id

        return vultr_config

    @classmethod
    def add_ssh_key_config(cls, public_key: str):
        return provisioner(
            "remote-exec",
            provisioner=provisioner(
                "remote-exec",
                inline=[
                    'mkdir -p ~/.ssh',
                    f"{public_key} >> ~/.ssh/authorized_keys"
                ],
            )
        )

    @classmethod
    def gen_ssh_conn_config(
            cls, *, ssh_user: str = DEFAULT_SSH_USER, ssh_private_key: str,
            ssh_host: str, ssh_port: int = DEFAULT_SSH_PORT
    ) -> dict:

        # see more in https://www.terraform.io/docs/provisioners/connection.html
        return {
            'type': 'ssh',
            'user': ssh_user,
            'private_key': ssh_private_key,
            'host': ssh_host,
            'port': ssh_port,
            'timeout': '30s'
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
        ssh_port: int = DEFAULT_SSH_PORT
    ):
        config = Terrascript()
        docker_provider = provider.docker(
            host=docker_host,
            connection=cls.gen_ssh_conn_config(
                ssh_user=ssh_user,
                ssh_private_key=ssh_private_key,
                ssh_host=ssh_host,
                ssh_port=ssh_port
            )
        )
        docker_image_resource = resource.docker_image(
            'nginx_image',
            name=cls.DEFAULT_NGINX_DOCKER_IMAGE,
        )
        docker_container_resource = resource.docker_container(
            'nginx_container',
            name=f"{site_name}-container-${{random_pet.docker_pet_name.id}}",
            image="${docker_image.nginx_image.latest}",
            restart="always",
            start=True,
            ports={
                'internal': 80
            },
            upload=[]
        )
        docker_name_resource = resource.random_pet(
            'docker_pet_name',
            length=1,
        )

        if template_tar_bytes:
            template_tar_file = f"{site_name}-tar-${{random_pet.docker_pet_name.id}}.tar.gz",
            template_tar_file_content = base64.b64encode(template_tar_bytes).decode('utf8')
            template_tar_path = f"{cls.DEFAULT_NGINX_DOCKER_CONTAINER_HTML_PATH}/${template_tar_file}"
            # self.upload_file(
            #     content='conf/myapp.conf',
            #     destination=f"{self.DEFAULT_UPLOAD_PATH}/${template_tar_file}",
            #     ssh_user=ssh_user,
            #     ssh_private_key=ssh_private_key,
            #     ssh_host=ssh_host,
            #     ssh_port=ssh_port
            # )
            docker_container_resource['upload'].append({
                'content_base64': template_tar_file_content,
                'file': template_tar_path
            })

        if script:
            entrypoint_sh_content = TemplateRender().render(
                cls.DEFAULT_NGINX_DOCKER_ENTRYPOINT_PATH,
                init_script_path=cls.DEFAULT_DOCKER_ENTRYPOINT_PATH,
                html_path=cls.DEFAULT_NGINX_DOCKER_CONTAINER_HTML_PATH
            )
            docker_container_resource['upload'].append({
                'content': entrypoint_sh_content,
                'file': cls.DEFAULT_DOCKER_ENTRYPOINT_PATH
            })

        config += docker_provider
        config += docker_image_resource
        config += docker_container_resource
        config += docker_name_resource

        return config

    def remote_exec(
            self, *, ssh_user: str = DEFAULT_SSH_USER, ssh_private_key: str,
            ssh_host: str, ssh_port: int = DEFAULT_SSH_PORT
    ):
        exec_config = Terrascript()
        ssh_conn = self.gen_ssh_conn_config(
            ssh_user=ssh_user,
            ssh_private_key=ssh_private_key,
            ssh_host=ssh_host,
            ssh_port=ssh_port
        )
        exec_resource = self.null_resource(
            'remote-exec',
            provisioner=provisioner(
                "remote-exec",
                inline=[
                    'ls -la'
                ],
                connection=ssh_conn
            )
        )

        exec_config += exec_resource
        return exec_config

    def upload_file(
        self, content: str, *, destination: str = DEFAULT_UPLOAD_PATH,
        ssh_user: str = DEFAULT_SSH_USER, ssh_private_key: str,
        ssh_host: str, ssh_port: int = DEFAULT_SSH_PORT
    ):
        upload_config = Terrascript()

        ssh_conn = self.gen_ssh_conn_config(
            ssh_user=ssh_user,
            ssh_private_key=ssh_private_key,
            ssh_host=ssh_host,
            ssh_port=ssh_port
        )
        file_resource = self.null_resource(
            'upload_file_resource',
            provisioner=provisioner(
                self.TERRAFORM_RESOURCE_FILE,
                content=content,
                destination=destination,
                connection=ssh_conn
            )
        )

        upload_config += file_resource
        return upload_config
