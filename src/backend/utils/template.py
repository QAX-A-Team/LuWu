from starlette.templating import Jinja2Templates


class TemplateRender:
    NGINX_TEMPLATE_CONF = 'nginx.conf'

    def __init__(self) -> None:
        self.templates = Jinja2Templates(directory="templates")

    def render(self, template, **tpl_data):
        if tpl_data is None:
            tpl_data = {}
        template = self.templates.get_template(template)
        content = template.render(**tpl_data)
        return content

    def render_nginx_conf(self, **tpl_data):
        return self.render(
            template=self.NGINX_TEMPLATE_CONF,
            **tpl_data
        )
