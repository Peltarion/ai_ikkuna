# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/stable/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../../'))
import sphinx_bootstrap_theme

# -- Project information -----------------------------------------------------

project = 'ikkuna'
copyright = '2018, Rasmus Diederichsen'
author = 'Rasmus Diederichsen'

# The short X.Y version
version = ''
# The full version, including alpha/beta/rc tags
release = '0'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx.ext.githubpages',
    # 'sphinx_autodoc_typehints',   # currently unpippable May 07, 2018
    'sphinx.ext.napoleon',
    'sphinxarg.ext',
    'sphinx.ext.viewcode'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path .
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'
highlight_language = 'python3'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'bootstrap'
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'navbar_class': 'navbar navbar-inverse',
    'bootswatch_theme': 'flatly'
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_logo = html_static_path[0] + '/logo.png'

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'ikkunadoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'ikkuna.tex', 'ikkuna Documentation',
     'Rasmus Diederichsen', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'ikkuna', 'ikkuna Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'ikkuna', 'ikkuna Documentation',
     author, 'ikkuna', 'A tool for monitoring neural network training',
     'Miscellaneous'),
]


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'python': ('https://docs.python.org/', None),
                       'matplotlib': ('https://matplotlib.org/', None),
                       'torch': ('https://pytorch.org/docs/master/', None),
                       'torchvision': ('https://pytorch.org/docs/master/', None)}

nitpick_ignore = [('py:mod', 'torchvision.datasets'),
                  ('py:meth', 'torchvision.models.alexnet'),
                  # These two occur when inheriting from Module. Dunno why.
                  ('py:class', 'torch.nn.modules.module.Module'),
                  ('py:class', 'Module'),
                  # This happens when inheriting from Sequential
                  ('py:class', 'torch.nn.modules.container.Sequential'),
                  ('py:class', 'function'),
                  ('py:class', 'torch.nn._Loss'),
                  ('py:class', 'torch.optim.lr_scheduler._LRScheduler'),
                  ('py:meth', 'torch.optim.lr_scheduler._LRScheduler.state_dict'),
                  ('py:meth', 'torch.optim.lr_scheduler._LRScheduler.load_state_dict'),
                  ]

autodoc_member_order = 'bysource'


def setup(app):
    '''
    Enable documenting 'special methods' using the autodoc_ extension.

    :param app: The Sphinx application object.

    This function connects the :func:`special_methods_callback()` function to
    ``autodoc-skip-member`` events.

    .. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
    '''
    app.connect('autodoc-skip-member', special_methods_callback)


def special_methods_callback(app, what, name, obj, skip, options):
    '''
    Enable documenting 'special methods' using the autodoc_ extension.

    Refer to :func:`enable_special_methods()` to enable the use of this
    function (you probably don't want to call
    :func:`special_methods_callback()` directly).

    This function implements a callback for ``autodoc-skip-member`` events to
    include documented 'special methods' (method names with two leading and two
    trailing underscores) in your documentation. The result is similar to the
    use of the ``special-members`` flag with one big difference: Special
    methods are included but other types of members are ignored. This means
    that attributes like ``__weakref__`` will always be ignored (this was my
    main annoyance with the ``special-members`` flag).

    The parameters expected by this function are those defined for Sphinx event
    callback functions (i.e. I'm not going to document them here :-).
    '''
    import types
    if getattr(obj, '__doc__', None) and isinstance(obj, (types.FunctionType, types.MethodType)):
        return False
    else:
        return skip
