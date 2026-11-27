{{- $p := .Params -}}
# {{ .Title }}

{{ with .Description }}> {{ . }}

{{ end -}}
- {{ i18n "by" }} : {{ site.Params.author }}, {{ site.Params.jobTitle }} ({{ site.Home.Permalink }})
{{ if .IsPage }}{{ if eq .Section "articles" }}- {{ .Date.Format "2006-01-02" }} ({{ i18n "updated_on" }} {{ .Lastmod.Format "2006-01-02" }})
{{ end }}{{ end -}}
- URL : {{ .Permalink }}
{{ with .Params.tags }}- {{ i18n "topics" }} : {{ delimit . ", " }}
{{ end }}{{ range .Translations }}- {{ .Language.Label }} : {{ .Permalink }}
{{ end }}
{{ with $p.tldr }}- **{{ i18n "tldr" }}** : {{ . }}
{{ end }}{{ with $p.problem }}- **{{ i18n "problem" }}** : {{ . }}
{{ end }}{{ with $p.context }}- **{{ i18n "context" }}** : {{ . }}
{{ end }}{{ with $p.constraints }}- **{{ i18n "constraints" }}** : {{ delimit . " ; " }}
{{ end }}{{ with $p.stack }}- **{{ i18n "stack" }}** : {{ delimit . ", " }}
{{ end }}{{ with $p.outcome }}- **{{ i18n "outcome" }}** : {{ . }}
{{ end }}
{{ .RawContent | strings.TrimSpace }}
{{ with $p.faq }}
## {{ i18n "faq" }}
{{ range . }}
### {{ .q }}

{{ .a }}
{{ end }}{{ end }}
