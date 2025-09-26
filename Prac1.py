class ShellEmulator:
    def __init__(self):
        self.vfs_name = "myvfs"
        self.running = True
        self.current_dir = "/"
    
    def print_prompt(self):
        print(f"{self.vfs_name}:{self.current_dir}$ ", end="")
    
    def parse_input(self, user_input):
        parts = user_input.strip().split()
        if not parts:
            return None, []
        command = parts[0]
        args = parts[1:]
        return command, args
    
    def cmd_ls(self, args):
        print(f"'ls', {args}")
    
    def cmd_cd(self, args):
        print(f"'cd' , : {args}")
          
    def cmd_exit(self):
        print("завершение работы")
        self.running = False
    
    def execute_command(self, command, args):
        command_methods = {
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'exit': self.cmd_exit,
        }
        
        if command in command_methods:
            command_methods[command](args)
        else:
            print(f"комманда '{command}' не найдена")
    
    def run(self):
        while self.running:
            self.print_prompt()
            user_input = input().strip()
            
            if not user_input:
                continue
            
            command, args = self.parse_input(user_input)
            
            if command is None:
                continue
            
            self.execute_command(command, args)
            print()

def main():

    shell = ShellEmulator()
    shell.run()

if __name__ == "__main__":
    main()