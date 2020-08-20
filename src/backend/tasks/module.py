from abc import ABC
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from typing import Union

from fabric import Connection

from crud.crud_config import crud_ssh_config
from crud.crud_module import crud_redirector
from crud.crud_module import crud_team_server
from db.session import session_manager
from tasks.base import BaseTask
from utils.template import TemplateRender


class BaseDeployTask(BaseTask, ABC):
    @classmethod
    def exec_remote_cmd(cls, conn: Connection, command: str, **kwargs):
        return conn.run(command, **kwargs)

    @classmethod
    def upload_remote_file(cls, conn: Connection, source_file: str, remote_file: str):
        return conn.put(source_file, remote_file)

    @classmethod
    def gen_ssh_connection(cls, private_key_path: str, addr: str):
        return Connection(
            addr,
            connect_kwargs={
                "key_filename": private_key_path,
            },
        )

    @classmethod
    def gen_tmp_file(cls, content: Union[str, bytes], dir_path: str, delete: bool = False):
        mode = 'wb' if isinstance(content, bytes) else 'wt'
        tmp_file = NamedTemporaryFile(mode=mode, dir=dir_path, delete=delete)
        tmp_file.write(content)
        tmp_file.seek(0)
        return tmp_file

    @classmethod
    def gen_ssh_conn(cls, addr: str, private_key: str, tmp_dir: str):
        tmp_ssh_private_key_file = NamedTemporaryFile(mode='wt', dir=tmp_dir, delete=False)
        tmp_ssh_private_key_file.write(str(private_key))
        tmp_ssh_private_key_file.seek(0)

        ssh_conn = cls.gen_ssh_connection(
            addr=addr,
            private_key_path=tmp_ssh_private_key_file.name
        )
        return ssh_conn


class DeployTeamServerTask(BaseDeployTask):
    name = 'deploy_team_server'

    def run(self, team_server_id: int):
        with session_manager() as db_session:
            team_server_obj = crud_team_server.get(db_session=db_session, id=team_server_id)
            ssh_obj = crud_ssh_config.get_config(db_session)
            if not ssh_obj:
                return

            tmp_dir = TemporaryDirectory()
            ssh_conn = self.gen_ssh_conn(
                addr=f"root@{team_server_obj.ip}",
                private_key=ssh_obj.private_key,
                tmp_dir=tmp_dir.name
            )
            # 1. install requirement
            install_lib_script = "apt-get install -y wget unzip"
            self.exec_remote_cmd(
                conn=ssh_conn,
                command=install_lib_script
            )

            # 2. download c2 profile , teamserver, cs
            template_render = TemplateRender()
            c2_content = team_server_obj.c2_profile.profile_content
            team_server_content = template_render.render(
                'scripts/team_server.sh', **{'port': team_server_obj.port}
            )
            cs_content = template_render.render(
                'scripts/cs_install.sh',
                cs_url=team_server_obj.cs_download_url,
                zip_pwd=team_server_obj.zip_password,
                cs_pwd=team_server_obj.password,
                kill_date=team_server_obj.kill_date
            )
            c2_tmp_file = self.gen_tmp_file(
                content=c2_content, dir_path=tmp_dir.name
            )
            team_server_file = self.gen_tmp_file(
                content=team_server_content, dir_path=tmp_dir.name
            )
            cs_server_file = self.gen_tmp_file(
                content=cs_content, dir_path=tmp_dir.name
            )
            self.upload_remote_file(
                conn=ssh_conn, source_file=c2_tmp_file.name, remote_file='ok.profile'
            )
            self.upload_remote_file(
                conn=ssh_conn, source_file=team_server_file.name, remote_file='teamserver'
            )
            self.upload_remote_file(
                conn=ssh_conn, source_file=cs_server_file.name, remote_file='cs.sh'
            )

            # 3. exec cs.sh
            self.exec_remote_cmd(conn=ssh_conn, command='chmod +x cs.sh && bash cs.sh')
            return self.set_result()


class DeployRedirectorTask(BaseDeployTask):
    name = 'deploy_redirector'

    def run(self, redirector_id: int):
        with session_manager() as db_session:
            redirector_obj = crud_redirector.get(db_session=db_session, id=redirector_id)
            ssh_obj = crud_ssh_config.get_config(db_session)
            if not ssh_obj:
                return

            tmp_dir = TemporaryDirectory()

            ssh_conn = self.gen_ssh_conn(
                addr=f"root@{redirector_obj.ip}",
                private_key=ssh_obj.private_key,
                tmp_dir=tmp_dir.name
            )

            template_render = TemplateRender()
            c2_content = redirector_obj.team_server.c2_profile.profile_content
            c2_tmp_file = self.gen_tmp_file(
                content=c2_content, dir_path=tmp_dir.name
            )
            self.upload_remote_file(
                conn=ssh_conn, source_file=c2_tmp_file.name, remote_file='c2.profile'
            )
            redirector_content = template_render.render(
                'scripts/c2_redirectors.sh',
                domain=redirector_obj.domain_name,
                ssl=1,
                c2_profile='~/c2.profile',
                cs2_server_ip=redirector_obj.team_server.cs_conn_url,
                redirect=redirector_obj.redirect_domain
            )
            redirector_bash_file = self.gen_tmp_file(
                content=redirector_content,
                dir_path=tmp_dir.name
            )
            self.upload_remote_file(
                conn=ssh_conn, source_file=redirector_bash_file.name, remote_file='redirector.sh'
            )
            self.exec_remote_cmd(conn=ssh_conn, command='chmod +x redirector.sh && bash redirector.sh')

