# -*- coding: utf-8 -*-
import logging

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy

from commercial.models import Category, CategoryProperties, ArticleProperties

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag
def get_price(article, user):
    return "%.02f" % article.get_price(user)

@register.simple_tag
def get_category_name(category, user):
    return CategoryProperties.objects.get(category=category, departament_id=user.profile.departament_id).name

@register.simple_tag
def get_article_name(article, user):
    return ArticleProperties.objects.get(article=article, departament_id=user.profile.departament_id).name

def get_cached_trees(queryset):
    """
    Takes a list/queryset of model objects in MPTT left (depth-first) order and
    caches the children and parent on each node. This allows up and down
    traversal through the tree without the need for further queries. Use cases
    include using a recursively included template or arbitrarily traversing
    trees.

    NOTE: nodes _must_ be passed in the correct (depth-first) order. If they aren't,
    a ValueError will be raised.

    Returns a list of top-level nodes. If a single tree was provided in its
    entirety, the list will of course consist of just the tree's root node.

    For filtered querysets, if no ancestors for a node are included in the
    queryset, it will appear in the returned list as a top-level node.

    Aliases to this function are also available:

    ``mptt.templatetags.mptt_tag.cache_tree_children``
       Use for recursive rendering in templates.

    ``mptt.querysets.TreeQuerySet.get_cached_trees``
       Useful for chaining with queries; e.g.,
       `Node.objects.filter(**kwargs).get_cached_trees()`
    """

    current_path = []
    top_nodes = []

    if queryset:
        # Get the model's parent-attribute name
        parent_attr = queryset[0].category._mptt_meta.parent_attr
        root_level = None
        is_filtered = hasattr(queryset, "query") and queryset.query.has_filters()
        for obj in queryset:
            # Get the current mptt node level
            node_level = obj.category.get_level()

            if root_level is None or (is_filtered and node_level < root_level):
                # First iteration, so set the root level to the top node level
                root_level = node_level

            elif node_level < root_level:
                # ``queryset`` was a list or other iterable (unable to order),
                # and was provided in an order other than depth-first
                raise ValueError(
                    gettext_lazy("Node %s not in depth-first order") % (type(queryset),)
                )

            # Set up the attribute on the node that will store cached children,
            # which is used by ``MPTTModel.get_children``
            obj._cached_children = []

            # Remove nodes not in the current branch
            while len(current_path) > node_level - root_level:
                current_path.pop(-1)

            if node_level == root_level:
                # Add the root to the list of top nodes, which will be returned
                top_nodes.append(obj)
            else:
                # Cache the parent on the current node, and attach the current
                # node to the parent's list of children
                _parent = current_path[-1]
                setattr(obj, parent_attr, _parent)
                _parent._cached_children.append(obj)

                if root_level == 0:
                    # get_ancestors() can use .parent.parent.parent...
                    setattr(obj, "_mptt_use_cached_ancestors", True)

            # Add the current node to end of the current path - the last node
            # in the current path is the parent for the next iteration, unless
            # the next iteration is higher up the tree (a new branch), in which
            # case the paths below it (e.g., this one) will be removed from the
            # current path during the next iteration
            current_path.append(obj)

    return top_nodes

@register.filter
def cache_tree_children(queryset):
    """
    Alias to `mptt.utils.get_cached_trees`.
    """

    return get_cached_trees(queryset)

class RecurseTreeNode(template.Node):
    def __init__(self, template_nodes, queryset_var):
        self.template_nodes = template_nodes
        self.queryset_var = queryset_var

    def _render_node(self, context, node):
        departament_id = node.departament_id
        bits = []
        context.push()
        if isinstance(node, Category):
            for child in node.get_children():
                child = CategoryProperties.objects.get(category=child, departament_id=departament_id)
                bits.append(self._render_node(context, child))
        elif isinstance(node, CategoryProperties):
            for child in node.category.get_children():
                child = CategoryProperties.objects.get(category=child, departament_id=departament_id)
                bits.append(self._render_node(context, child))
        context["node"] = node
        context["children"] = mark_safe("".join(bits))
        rendered = self.template_nodes.render(context)
        context.pop()
        return rendered

    def render(self, context):
        queryset = self.queryset_var.resolve(context)
        roots = cache_tree_children(queryset)
        bits = [self._render_node(context, node) for node in roots]
        return "".join(bits)


@register.tag
def recursetree(parser, token):
    """
    Iterates over the nodes in the tree, and renders the contained block for each node.
    This tag will recursively render children into the template variable {{ children }}.
    Only one database query is required (children are cached for the whole tree)

    Usage:
            <ul>
                {% recursetree nodes %}
                    <li>
                        {{ node.name }}
                        {% if not node.is_leaf_node %}
                            <ul>
                                {{ children }}
                            </ul>
                        {% endif %}
                    </li>
                {% endrecursetree %}
            </ul>
    """
    bits = token.contents.split()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(gettext_lazy("%s tag requires a queryset") % bits[0])

    queryset_var = template.Variable(bits[1])

    template_nodes = parser.parse(("endrecursetree",))
    parser.delete_first_token()

    return RecurseTreeNode(template_nodes, queryset_var)
