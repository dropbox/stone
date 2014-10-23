# babelapi(jinja2)

{% macro host(op) %}
{%- if op.extras['host'] == 'content' -%}
Dropbox::API::API_CONTENT_SERVER
{%- else -%}
Dropbox::API::API_SERVER
{%- endif -%}
{% endmacro %}

{% macro url_path(fields) %}
{%- if fields and fields[0].name == 'path' -%}
/#{ format_path(path, true) }
{%- endif -%}
{% endmacro %}

{% macro binary(op) %}
{%- if op.request_segmentation.segments[1] -%}
, {}, {{ op.request_segmentation.segments[1].name|lower }}
{%- endif -%}
{% endmacro %}

{% macro operation_def(namespace_name, op, indent_spaces) %}
{% filter indent(indent_spaces, indentfirst=True) %}
{% set request_fields = op.request_segmentation.segments[0].data_type.fields %}
# {{ op.doc|default('', True)|wordwrap(70)|default('', True)|replace('\n', '\n# ') }}
#
# Args:
{% for field in op.request_segmentation.segments[0].data_type.fields %}
# * +{{ field.name }}+{% if field.data_type %} (+{{ field.data_type }}+){% endif %}:
#   {{ field.doc|default('', True)|wordwrap(70)|default('', True)|replace('\n', '\n#   ') }}
{% endfor %}
#
# Returns:
#   {{ op.response_segmentation.segments[0].data_type.name|class }}
{# hack: assume there's only one input struct with an optional binary (called data) after it #}
{# hack: assume if path is the first field of the input struct, it should be appended to the URL #}
{# hack: assume if there's more than one field in the response, then the first one is a struct and the second is binary #}
def {{ op.name|method }}(
  {%- if op.request_segmentation.segments[0].data_type.fields|length > 0 -%}
    {{ op.request_segmentation.segments[0].data_type.fields|join(' = nil, ', 'name') }} = nil
    {%- if op.request_segmentation.segments[1] -%}
      , {{ op.request_segmentation.segments[1].name|lower }} = nil
    {%- endif -%}
  {%- endif -%}
  )
  input = {
    {% for field in op.request_segmentation.segments[0].data_type.fields %}
      {% if field.name != 'path' %}
    {{ field.name }}: {{ field.name }},
      {% endif %}
    {% endfor %}
  }
  response = @session.do_{{ op.extras['method']|lower }}({%- trim -%}
    {{ host(op) }}, "{{ op.path }}{{ url_path(request_fields) }}", input{{ binary(op) }})
  {% if op.response_segmentation.segments|length > 1 %}
  parsed_response = Dropbox::API::HTTP.parse_response(response, true)
  metadata = parse_metadata(response)
  return parsed_response, metadata
  {% else %}
  Dropbox::API::{{ op.response_segmentation.segments[0].data_type.name|class }}{%- trim -%}
      .from_hash(Dropbox::API::HTTP.parse_response(response))
  {% endif %}
end

{% endfilter %}
{% endmacro %}

module Dropbox
  module API

    # Use this class to make Dropbox API calls.  You'll need to obtain an OAuth 2 access token
    # first; you can get one using either WebAuth or WebAuthNoRedirect.
    class Client

      # Args:
      # * +oauth2_access_token+: Obtained via DropboxOAuth2Flow or DropboxOAuth2FlowNoRedirect.
      # * +locale+: The user's current locale (used to localize error messages).
      def initialize(oauth2_access_token, client_identifier = '', root = 'auto', locale = nil)
        unless oauth2_access_token.is_a?(String)
          fail ArgumentError, "oauth2_access_token must be a String; got #{ oauth2_access_token.inspect }"
        end
        @session = Dropbox::API::Session.new(oauth2_access_token, client_identifier, locale)
        @root = root.to_s  # If they passed in a symbol, make it a string

        unless ['dropbox', 'app_folder', 'auto'].include?(@root)
          fail ArgumentError, 'root must be "dropbox", "app_folder", or "auto"'
        end

        # App Folder is the name of the access type, but for historical reasons
        # sandbox is the URL root component that indicates this
        if @root == 'app_folder'
          @root = 'sandbox'
        end
      end

      {% for namespace_name, namespace in api.namespaces.items() %}
        {% for op in namespace.operations %}
          {{- operation_def(namespace_name, op, 6) }}
        {% endfor %}
      {% endfor %}

      private

      # From the oauth spec plus "/".  Slash should not be ecsaped
      RESERVED_CHARACTERS = /[^a-zA-Z0-9\-\.\_\~\/]/  # :nodoc:

      def format_path(path, escape = true) # :nodoc:
        # replace multiple slashes with a single one
        path.gsub!(/\/+/, '/')

        # ensure the path starts with a slash
        path.gsub!(/^\/?/, '/')

        # ensure the path doesn't end with a slash
        path.gsub!(/\/?$/, '')

        escape ? URI.escape(path, RESERVED_CHARACTERS) : path
      end

      # Parses out file metadata from a raw dropbox HTTP response.
      #
      # Args:
      # * +response+: The raw, unparsed HTTPResponse from Dropbox.
      #
      # Returns:
      # * The metadata of the file as a hash.
      def parse_metadata(response) # :nodoc:
        begin
          raw_metadata = response['x-dropbox-metadata']
          metadata = JSON.parse(raw_metadata)
        rescue
          raise DropboxError.new("Dropbox Server Error: x-dropbox-metadata=#{raw_metadata}",
                       response)
        end
        return metadata
      end

    end
  end
end