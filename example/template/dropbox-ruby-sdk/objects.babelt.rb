# babelsdk(jinja2)

require 'date'

{% macro object_def(data_type, indent_spaces) %}
{% if data_type.composite_type == 'struct' and not data_type.name.endswith('Request') %}
{% filter indent(indent_spaces, indentfirst=True) %}
# {{ data_type.doc|replace('\n', '\n    # ')|wordwrap }}
#
# Fields:
{% for field in data_type.fields %}
# * +{{ field.name }}+{% if field.data_type %} (+{{ field.data_type.name }}+){% endif %}:
#   {{ field.doc|default('', True)|wordwrap(70)|default('', True)|replace('\n', '\n#   ') }}
{% endfor %}
# * +opts+:
#   Ignored
class {{ data_type.name }}{% if data_type.super_type %} < {{ data_type.super_type.name }}{% endif %}

  {% for field in data_type.fields %}
  attr_accessor :{{ field.name }}
  {% endfor %}

  def initialize(
    {% for field in data_type.all_fields %}
      {{ field.name }}{% if field.nullable %} = nil{% endif %},
    {% endfor %}
      opts = {}
  )
  {% for field in data_type.all_fields %}
    @{{ field.name }} = {{ field.name }}
  {% endfor %}
  end

  def self.from_hash(hash)
    self.new(
    {% for field in data_type.all_fields %}
      {% if field.data_type.composite_type and field.nullable %}
      hash.include?('{{ field.name }}') && hash['{{ field.name }}'] ? {{ field.data_type.name }}.from_hash(hash['{{ field.name }}']) : nil,
      {% elif field.data_type.composite_type %}
      {{ field.data_type.name }}.from_hash(hash['{{ field.name }}']),
      {% elif field.data_type.name == 'Timestamp' %}
      hash.include?('{{ field.name }}') ? Dropbox::API::convert_date(hash['{{ field.name }}']) : nil,
      {% elif field.data_type.name == 'List' and field.data_type.data_type.composite_type %}
      hash['{{ field.name }}'].collect { |elem| {{ field.data_type.data_type.name }}.from_hash(elem) },
      {% else %}
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
      Date.strptime(str, '%a, %d %b %Y %H:%M:%S +0000')
    end

    {% for namespace in api.namespaces.values() %}
        {% for data_type in namespace.data_types %}
          {{- object_def(data_type, 4) }}
        {% endfor %}
    {% endfor %}
  end
end