# babelapi(jinja2)

require 'date'

{% macro arg_list(args) -%}
{% for arg in args %}
{{ arg.name }}{% if arg.has_default %} = {{ arg.default|pprint }}{% elif arg.optional %} = nil{% endif %},
{% endfor %}
{%- endmacro %}

{% macro object_def(data_type, indent_spaces) %}
{% if data_type.composite_type == 'struct' and not data_type.name.endswith('Request') %}
{% filter indent(indent_spaces, indentfirst=True) %}
{% if data_type.doc %}
# {{ data_type.doc|wordwrap(70)|replace('\n', '\n# ') }}
#
{% endif %}
# Fields:
{% for field in data_type.fields %}
# * +{{ field.name }}+{% if field.data_type %} (+{{ field.data_type.name }}+){% endif %}:
#   {{ field.doc|default('', True)|wordwrap(70)|replace('\n', '\n#   ') }}
{% endfor %}
class {{ data_type.name|class }}{% if data_type.super_type %} < {{ data_type.super_type.name|class }}{% endif %}

  attr_accessor(
      {{ data_type.fields|map(attribute='name')|map('inverse_format', ':{0}')|join(',\n      ') }}
  )

  def initialize(
    {{ arg_list(data_type.all_fields)|indent(4)|string_slice(0, -1) }}
  )
  {% for field in data_type.all_fields %}
    @{{ field.name }} = {{ field.name }}
  {% endfor %}
  end

  def self.from_hash(hash)
    self.new(
    {% for field in data_type.all_fields %}
      {%+ if field.nullable -%}
      hash['{{ field.name }}'].nil? ? nil :{{ ' ' }}
      {%- elif field.optional -%}
      !hash.include?('{{ field.name }}') ? nil :{{ ' ' }}
      {%- endif %}
      {% if field.data_type.composite_type -%}
      {{ field.data_type.name|class }}.from_hash(hash['{{ field.name }}']),
      {% elif field.data_type.name == 'Timestamp' -%}
      Dropbox::API::convert_date(hash['{{ field.name }}']),
      {% elif field.data_type.name == 'List' and field.data_type.data_type.composite_type -%}
      hash['{{ field.name }}'].collect { |elem| {{ field.data_type.data_type.name }}.from_hash(elem) },
      {% else -%}
      hash['{{ field.name }}'],
      {% endif %}
    {% endfor %}
    )
  end
end

{% endfilter %}
{% endif %}
{% endmacro %}

module Dropbox
  module API

    # Converts a string date to a Date object
    def self.convert_date(str)
      DateTime.strptime(str, '%a, %d %b %Y %H:%M:%S +0000')
    end

    {% for namespace in api.namespaces.values() %}
        {% for data_type in namespace.data_types %}
          {{- object_def(data_type, 4) }}
        {% endfor %}
    {% endfor %}
  end
end