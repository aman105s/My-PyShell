import cmd, sys, os, shutil, subprocess, shlex, readline, re

BUILTINS = {"exit", "type", "echo", "pwd", "cd", "history","jobs","complete","declare"}

last_appended = 0
HISTFILE = os.environ.get("HISTFILE")  
background_jobs = []
COMPLETIONS = {}
SHELL_VARIABLES = {}

def is_valid_identifier(name):
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is not None

def expand_variables(parts):
    expanded = []

    for part in parts:

        # Expand ${VAR}
        part = re.sub(
            r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
            lambda m: SHELL_VARIABLES.get(m.group(1), ""),
            part,
        )

        # Expand $VAR
        part = re.sub(
            r"\$([A-Za-z_][A-Za-z0-9_]*)",
            lambda m: SHELL_VARIABLES.get(m.group(1), ""),
            part,
        )

        #remove empty words
        if part != "":
            expanded.append(part)

    return expanded

def longest_common_prefix(strings):
    if not strings:
        return ""

    prefix = strings[0]

    for s in strings[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""

    return prefix

def completer(text, state):
    line = readline.get_line_buffer()

    # Split on whitespace only (don't use shlex here)
    words = line.split()

    if words and words[0] in COMPLETIONS:
        command = words[0]
        current = words[-1]
        previous = words[-2] if len(words) > 1 else ""

        if command in COMPLETIONS:

            env = os.environ.copy()
            env["COMP_LINE"] = line
            env["COMP_POINT"] = str(len(line.encode()))

            result = subprocess.run(
                [
                    COMPLETIONS[command],
                    command,
                    current,
                    previous,
                 ],
                capture_output=True,
                text=True,
                env=env,
            )

            matches = [
                line.strip() + " "
                for line in result.stdout.splitlines()
                if line.strip()
            ]

            if state < len(matches):
                return matches[state]

            return None
    
    # Completing the command name
    if len(words) <= 1 and not line.endswith(" "):
        commands = list(BUILTINS)

        for directory in os.environ.get("PATH", "").split(os.pathsep):
            try:
                commands.extend(os.listdir(directory))
            except OSError:
                pass

        matches = sorted(set(cmd for cmd in commands if cmd.startswith(text)))

        if len(matches) == 1:
            matches[0] += " "
    # Completing a filename
    else:
        dirname, prefix = os.path.split(text)

        search_dir = dirname if dirname else "."

        matches = []

        try:
            for name in os.listdir(search_dir):
                if name.startswith(prefix):
                    # Only prepend dirname if the user actually typed one
                    candidate = os.path.join(dirname, name) if dirname else name

                    if os.path.isdir(os.path.join(search_dir, name)):
                        matches.append(candidate + "/")
                    else:
                        matches.append(candidate + " ")
        except OSError:
            pass

        matches.sort()

    if state < len(matches):
        return matches[state]
    return None

def display_matches(substitution, matches, longest_match_len):
    print()
    print("  ".join(sorted(matches)))

    sys.stdout.write("$ " + readline.get_line_buffer())
    sys.stdout.flush()

readline.parse_and_bind("tab: complete")
readline.set_completer(completer)


def reap_jobs(print_done=True):
    global background_jobs

    remaining = []

    total = len(background_jobs)

    for i, job in enumerate(background_jobs):

        # Marker
        if total == 1:
            marker = "+"
        elif i == total - 1:
            marker = "+"
        elif i == total - 2:
            marker = "-"
        else:
            marker = " "

        if job["process"].poll() is None:
            remaining.append(job)
        else:
            print(
                f'[{job["job_id"]}]{marker}  {"Done":<24}{job["command"]}'
            )
            job["process"].wait()      # reap zombie

    background_jobs = remaining


def next_job_number():
    if not background_jobs:
        return 1

    return max(job["job_id"] for job in background_jobs) + 1


def execute(parts, stdin=None, stdout=None, background=False):
    cmd = parts[0]
    global last_appended
    
    # Builtins
    if cmd == "echo":
        print(" ".join(parts[1:]), file=stdout or sys.stdout)
        return

    elif cmd == "pwd":
        print(os.getcwd(), file=stdout or sys.stdout)
        return

    elif cmd == "type":
        target = parts[1]

        if target in BUILTINS:
            print(f"{target} is a shell builtin", file=stdout or sys.stdout)

        elif path := shutil.which(target):
            print(f"{target} is {path}", file=stdout or sys.stdout)

        else:
            print(f"{target}: not found", file=stdout or sys.stdout)

        return

    elif cmd == "cd":

        if len(parts) < 2:
            return

        path = os.path.expanduser(parts[1])

        try:
            os.chdir(path)
        except FileNotFoundError:
            print(f"cd: {path}: No such file or directory")
        except NotADirectoryError:
            print(f"cd: {path}: Not a directory")
        except PermissionError:
            print(f"cd: {path}: Permission denied") 
        return

    
    elif cmd == "complete":
            
            # Register
            if len(parts) == 4 and parts[1] == "-C":
                COMPLETIONS[parts[3]] = parts[2]
                return

            # Remove
            if len(parts) == 3 and parts[1] == "-r":
                COMPLETIONS.pop(parts[2], None)
                return

            # Print
            if len(parts) == 3 and parts[1] == "-p":

                command = parts[2]

                if command in COMPLETIONS:
                    print(
                        f"complete -C '{COMPLETIONS[command]}' {command}",
                        file=stdout or sys.stdout,
                    )
                else:
                    print(
                        f"complete: {command}: no completion specification",
                        file=stdout or sys.stdout,
                    )

                return

    elif cmd == "declare":
        # declare -p NAME
        if len(parts) == 3 and parts[1] == "-p":
            name = parts[2]

            if name in SHELL_VARIABLES:
                print(
                    f'declare -- {name}="{SHELL_VARIABLES[name]}"',
                    file=stdout or sys.stdout,
                )
            else:
                print(
                    f"declare: {name}: not found",
                    file=stdout or sys.stdout,
                )
            return
        
        # declare NAME=VALUE
        if len(parts) == 2 and "=" in parts[1]:

            assignment = parts[1]
            name, value = assignment.split("=", 1)

            if not is_valid_identifier(name):
                print(
                    f"declare: `{assignment}': not a valid identifier",
                    file=stdout or sys.stdout,
                )
                return

            SHELL_VARIABLES[name] = value
            return


    elif cmd == "jobs":
        total = len(background_jobs)

        remaining = []

        for i, job in enumerate(background_jobs):

            if total == 1:
                marker = "+"
            elif i == total - 1:
                marker = "+"
            elif i == total - 2:
                marker = "-"
            else:
                marker = " "

            if job["process"].poll() is None:
                print(
                    f'[{job["job_id"]}]{marker}  {"Running":<24}{job["command"]} &'
                )
                remaining.append(job)

            else:
                print(
                    f'[{job["job_id"]}]{marker}  {"Done":<24}{job["command"]}'
                )
                job["process"].wait()

        background_jobs[:] = remaining
        return
    
    elif cmd == "history":
        history_len = readline.get_current_history_length()
        #history -r <file>
        if len(parts) == 3 and parts[1] == "-r":
            try:
                readline.read_history_file(parts[2])
                last_appended = readline.get_current_history_length()
            except FileNotFoundError:
                print(f"history: {parts[2]}: No such file or directory",
                    file=stdout or sys.stdout)
            return

         # history -w <file>
        if len(parts) == 3 and parts[1] == "-w":
            try:
                readline.write_history_file(parts[2])
                last_appended = readline.get_current_history_length()
            except OSError as e:
                print(f"history: {e}", file=stdout or sys.stdout)
            return
        
        #history -a <file>
        if len(parts) == 3 and parts[1] == "-a":

            current = readline.get_current_history_length()
            count = current - last_appended

            if count > 0:
                readline.append_history_file(count, parts[2])
                last_appended = current
            return



        #Default Show all history if no argument is provided
        start = 1

        #history <n>
        if len(parts) > 1:
            try:
                n = int(parts[1])
                start = max(1, history_len - n + 1)
            except ValueError:
                print(f"history: {parts[1]}: numeric argument required")
                return
        
        for i in range(start, history_len + 1):
            print(f"{i}  {readline.get_history_item(i)}", file=stdout or sys.stdout)
        return

            

    # External command
    executable = shutil.which(cmd)

    if executable is None:
        print(f"{cmd}: command not found")
        return

    if background:
        process = subprocess.Popen(
            parts,
            executable=executable,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            text=True,
        )

        job_id = next_job_number()

        print(f"[{job_id}] {process.pid}")

        background_jobs.append({
            "job_id": job_id,
            "process": process,
            "command": " ".join(parts)
        })

    else:
        subprocess.run(
            parts,
            executable=executable,
            stdin=stdin,
            stdout=stdout,
            text=True,
        )


def run_pipe(command):
    commands = [shlex.split(cmd.strip()) for cmd in command.split("|")]

    prev_stdout = None
    processes = []

    for i, parts in enumerate(commands):
        last = i == len(commands) - 1

        if parts[0] in BUILTINS:

            if last:
                execute(parts, stdin=prev_stdout, stdout=sys.stdout)

                if prev_stdout:
                    prev_stdout.close()

                break

            r, w = os.pipe()

            with os.fdopen(w, "w") as wf:
                execute(parts, stdin=prev_stdout, stdout=wf)

            if prev_stdout:
                prev_stdout.close()

            prev_stdout = os.fdopen(r)

        else:
            executable = shutil.which(parts[0])

            if executable is None:
                print(f"{parts[0]}: command not found")
                return

            p = subprocess.Popen(
                parts,
                executable=executable,
                stdin=prev_stdout,
                stdout=None if last else subprocess.PIPE,
                text=True,
            )

            if prev_stdout:
                prev_stdout.close()

            if not last:
                prev_stdout = p.stdout

            processes.append(p)

    for p in processes:
        p.wait()

    if prev_stdout:
        prev_stdout.close()


def main():

    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n")
    readline.set_completer(completer)
    readline.set_completion_display_matches_hook(display_matches)
    readline.set_auto_history(True)

    global last_appended

    if HISTFILE:
        try:
            readline.read_history_file(HISTFILE)
            last_appended = readline.get_current_history_length()
        except OSError:
            pass

    while True:
        reap_jobs(print_done=True)

        command = input("$ ")

        if ">" in command or "1>" in command:
            os.system(command)
            continue



        if command == "exit":
            if HISTFILE:
                try:
                    readline.write_history_file(HISTFILE)
                except OSError:
                    pass
            break

        elif "|" in command:
            run_pipe(command)
            continue
        
        else:
            parts = shlex.split(command)

            background = False

            if parts and parts[-1] == "&":
                background = True
                parts.pop()

            parts = expand_variables(parts)

            execute(parts, background=background)


if __name__ == "__main__":
    main()