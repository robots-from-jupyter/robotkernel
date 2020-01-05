{# usage: jupyter nbconvert --to html --TemplateExporter.exclude_input=True --TemplateExporter.exclude_input_prompt=True --TemplateExporter.exclude_output_prompt=True --TemplateExporter.template_file=nbconvert.tpl notebook.ipynb #}
{% extends 'full.tpl'%}
{% block header %}
  {{ super() }}
  <style type="text/css">
  body, div#notebook { padding: 0; }
  .output_png.output_subarea { padding: 1em 0 0 0; }
  .rendered_html ul:not(.list-inline) { padding-left: 0; }
  .rendered_html ul:not(.list-inline) li { margin-bottom: 1em; }
  .rendered_html ul:not(.list-inline) li:before {
    content: "–"; position: absolute; left: -1ex;
  }
  </style>
{% endblock header %}
{% block any_cell %}
{% if cell['cell_type'] != 'code' %}
  {{ super() }}
{% elif cell['outputs']|length > 2 %}
  {# drop log and report links output: #}
  {{ cell['outputs'].pop(0) and cell['outputs'].pop(0) and super() }}
{% elif cell['outputs']|length > 0 %}
  {# drop log and report links output: #}
  {{ cell['outputs'].pop(0) and super() }}
{% else %}
  {{ super() }}
{% endif %}
{% endblock any_cell %}
