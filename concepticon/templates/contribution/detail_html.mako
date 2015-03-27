<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "contributions" %>

<%def name="sidebar()">
    <%util:well>
        <h4>Compilers</h4>
            <ul class="unstyled">
            % for c in ctx.primary_contributors:
            <li>
                ${h.link(request, c)}
            </li>
            % endfor
        </ul>
        <h4>Source</h4>
        <ul class="unstyled">
            % for ref in ctx.references:
            <li>
                ${h.link(request, ref.source)}
                % if ref.source.files:
                    [${h.external_link(ref.source._files[0].jsondata['url'], label='PDF')}]
                % endif
            </li>
            % endfor
        </ul>
        <h4>Note</h4>
        <p>
            ${u.link_conceptlists(request, ctx.description)|n}
        </p>
        % if ctx.data:
            <dl>
                % for d in ctx.data:
                <dt>${d.key.capitalize()}</dt>
                <dd>
                    % if d.key == 'url':
                    ${h.external_link(d.value)}
                    % else:
                    ${d.value}
                    % endif
                </dd>
                % endfor
            </dl>
        % endif
    </%util:well>
</%def>

<h2>${_('Contribution')} ${ctx.name}</h2>

${request.get_datatable('values', h.models.Value, contribution=ctx).render()}