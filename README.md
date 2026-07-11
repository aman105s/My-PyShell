# My-PyShell 🐚

A lightweight POSIX-inspired shell written in Python.

My-PyShell is a command-line shell built from scratch to understand how Unix shells work internally. It supports command parsing, built-in commands, process creation, pipes, redirections, job control, programmable completion, shell variables, and parameter expansion.

> This project is intended as an educational implementation of a Unix-like shell and demonstrates core operating system concepts such as process management, inter-process communication, command parsing, and terminal interaction.

---

## ✨ Features

### Built-in Commands
- `cd`
- `pwd`
- `echo`
- `type`
- `exit`
- `history`
- `jobs`
- `complete`
- `declare`

---

### Process Execution
- Execute external programs from `$PATH`
- Command lookup using `PATH`
- Interactive shell prompt
- Proper command parsing using `shlex`

---

### Pipes & Redirection
- Multi-stage pipelines (`|`)
- Output redirection (`>`, `1>`)
- Built-in commands inside pipelines

Example:

```sh
echo hello | wc
cat file.txt | grep error | wc -l
```

---

### Background Jobs

Supports background execution using `&`

```sh
sleep 30 &
```

Implemented features:

- Background execution
- Job table
- `jobs` builtin
- Running/Done job states
- Automatic reaping
- Job number recycling
- Current (`+`) and previous (`-`) job markers

---

### Command History

- Command history
- Up-arrow navigation
- Persistent history
- `history`
- `history N`
- `history -r`
- `history -w`
- `history -a`
- `HISTFILE` support

---

### Auto Completion

#### Command completion

```text
ec<TAB>
```

↓

```text
echo
```

#### File completion

```text
cat rea<TAB>
```

↓

```text
cat README.md
```

#### Programmable completion

Supports Bash-style:

```sh
complete -C /path/to/script git
complete -p git
complete -r git
```

Features:

- Registered completer scripts
- Longest Common Prefix (LCP) completion
- Multiple completion candidates
- `COMP_LINE`
- `COMP_POINT`

---

### Shell Variables

Supports

```sh
declare foo=bar
declare -p foo
```

Variable validation

```sh
declare _VAR=value
```

Invalid identifiers

```sh
declare 123=value
```

---

### Parameter Expansion

Supports

```sh
$VAR
${VAR}
```

Examples

```sh
declare name=World

echo Hello $name
echo ${name}
echo ${missing}text
```

---

## 🛠️ Technologies Used

- Python 3
- `subprocess`
- `readline`
- `shlex`
- `os`
- `re`

---

## 📂 Project Structure

```
My-PyShell/
│
├── app/
│   └── main.py
│
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 🚀 Running

Clone the repository

```bash
git clone https://github.com/aman105s/My-PyShell.git
cd My-PyShell
```

Run

```bash
python3 -m app.main
```

or

```bash
uv run -m app.main
```

---

## 📸 Demo

```text
$ declare USER=Aman

$ echo Hello $USER
Hello Aman

$ sleep 10 &
[1] 24581

$ jobs
[1]+ Running                 sleep 10 &

$ echo hello | wc
1 1 6
```

---

## 📚 What I Learned

Building this shell helped me understand:

- Process creation (`fork`/`exec` concepts through Python)
- Pipes and inter-process communication
- Job control
- Shell parsing
- Terminal interaction
- Environment variables
- Command completion
- Parameter expansion
- Unix shell behavior

---

## 🔮 Future Improvements

- Input redirection (`<`)
- Here documents (`<<`)
- Quotes and escaping improvements
- Aliases
- Functions
- Environment variable export
- Signal handling (`Ctrl+C`, `Ctrl+Z`)
- Command substitution
- Arithmetic expansion

---

## 👨‍💻 Author

**Aman Kumar**

- GitHub: https://github.com/aman105s
- LinkedIn: https://www.linkedin.com/in/aman105s/

---

## 🙏 Acknowledgements

This project was developed as part of my journey to better understand how Unix shells work internally.

The implementation was inspired by and built while working through the excellent **Build Your Own Shell** challenge by **CodeCrafters**, which provides a structured, hands-on approach to implementing shell features from scratch.

While the code and implementation are my own, the challenge served as the roadmap that guided the development process.

If you're interested in systems programming, I highly recommend checking out CodeCrafters:
https://codecrafters.io