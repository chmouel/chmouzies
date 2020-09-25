#! /bin/sh

for source in "$@"; do
    case $source in
	*ChangeLog|*changelog) 
        source-highlight --failsafe -f esc --lang-def=changelog.lang --style-file=esc256.style -i "$source" ;;
	*Makefile|*makefile) 
        source-highlight --failsafe -f esc --lang-def=makefile.lang --style-file=esc256.style -i "$source" ;;
	*.tar|*.tgz|*.gz|*.bz2|*.xz)
        lesspipe.sh "$source" ;;
    *.json)
        jq -C '.' ${source};;
    *.md|*.yaml)
        pygmentize -O colorful  "$source";;
    # *) source-highlight --failsafe --infer-lang -f esc --style-file=esc.style -i "$source" ;;
    *)  chroma --formatter="terminal256" --style=vim ${source} ;;
    esac
done
