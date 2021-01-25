from django import template
from django.template.base import Node


register = template.Library()


@register.tag
def profile(parser, tags):
    nodelist = parser.parse(('endprofile',))
    parser.delete_first_token()
    return ProfileNode(nodelist, tags)


class ProfileNode(Node):
    def __init__(self, nodelist, tags):
        self.nodelist = nodelist
        self.block_name = tags.contents.split(' ')[1].strip("'")

    def __str__(self):
        return f"Profile {self.block_name}"

    def render(self, context):
        result = self.nodelist.render(context)
        return result
