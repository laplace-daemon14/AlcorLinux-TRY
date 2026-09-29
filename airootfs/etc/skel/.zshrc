ZSH=$HOME/.oh-my-zsh
ZSH_THEME="gnzh"


DISABLE_AUTO_UPDATE="true"
DISABLE_GIT_STATUS_TRACKING="true"
COMPLETION_WAITING_DOTS="true"


plugins=(git colored-man-pages extract history-substring-search encode64 web-search)

source $ZSH/oh-my-zsh.sh

export HISTCONTROL=ignoreboth:erasedups
export TERM=xterm-256color


alias sublime="subl"
alias s="subl"
alias zshconfig="subl ~/.zshrc"
alias show_open_ports="sudo lsof -i -n -P"
alias open_ports="show_open_ports"
alias show_public_ip="curl -Ss icanhazip.com"
alias public_ip="show_public_ip"
alias show_public_ip_v4="curl -Ss4 icanhazip.com/v4"
alias public_ip_v4="show_public_ip_v4"
alias show_public_ip_v6="curl -Ss6 icanhazip.com/v6"
alias public_ip_v6="show_public_ip_v6"
alias g++='g++ --std=c++11'
alias clang++='clang++ --std=c++11'
alias r2='r2 -AA'

alias grep="grep --color=auto"

highlight() {
    grep -E "$|$1" --color $2
}

scat() {
  for arg in "$@"; do
    pygmentize -g "$arg" 2> /dev/null || cat "$arg"
  done
}

mkcd() {
  if [ ! -n "$1" ]; then
    echo "Enter a directory name"
  elif [ -d $1 ]; then
    echo "\`$1' already exists"
  else
    mkdir $1 && cd $1
  fi
}

transfer() {
    if [ $# -eq 0 ]; then
        echo "No arguments specified. Usage:\ntransfer /tmp/test.md\ncat /tmp/test.md | transfer test.md"
        return 1
    fi

    file=$1
    tmpfile=$(mktemp -t transferXXX)
    basefile=$(basename "$file" | sed -e 's/[^a-zA-Z0-9._-]/-/g')

    if [ -t 0 ]; then
        if [ ! -e $file ]; then
            echo "File $file doesn't exists."
            return 1
        fi

        if [ -d $file ]; then
            zipfile=$(mktemp -t transferXXX.zip)
            cd $(dirname $file) && zip -r -q - $(basename $file) >> $zipfile
            curl --progress-bar --upload-file "$zipfile" "https://transfer.sh/$basefile.zip" >> $tmpfile
            rm -f $zipfile
        else
            curl --progress-bar --upload-file "$file" "https://transfer.sh/$basefile" >> $tmpfile
        fi
    else
        curl --progress-bar --upload-file - "https://transfer.sh/$basefile" >> $tmpfile
    fi

    cat $tmpfile
    rm -f $tmpfile
}

pdfbuild() {
    if [ $# -eq 0 ]
      then
        echo "No arguments supplied"
        return 1
    fi
    pdflatex $1 && biber ${1%.*} && pdflatex $1 && pdflatex $1
}

markdown2pdf() {
  if [ ! -n "$1" -o ! -f "$1" ]; then
    echo "Provide an existing input markdown file"
  elif [ ! "${1##*.}" = "md" ]; then
    echo "Provided file is no markdown file!"
  else
    pandoc $1 -f markdown -t latex -s -o ${1%.*}.pdf
  fi
}

compinit
xhost +local:docker &>/dev/null
