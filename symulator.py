from tkinter import *
from tkinter import ttk, filedialog, messagebox

# Define available commands and registers
COMMANDS = ["MOV", "ADD", "SUB"]
REGISTERS = ["AH", "AL", "BH", "BL", "CH", "CL", "DH", "DL"]


class SubRegister:
    def __init__(self, dec_value, bin_value):
        self.dec_value = 0
        self.bin_value = bin_value
        self.hex_value = hex(dec_value)


class Register(SubRegister):
    def __init__(self, dec_value, bin_value):
        super().__init__(dec_value, bin_value)
        self.h_register = SubRegister(0, f'{0:08b}')
        self.l_register = SubRegister(0, f'{0:08b}')


class Simulator:
    def __init__(self):
        # Init main window of the application
        self.main_window = Tk()
        self.main_window.title("Simple Microprocessor Simulator")
        self.main_window.geometry("800x600")
        self.main_window.resizable(False, False)

        # Init code editor space
        self.code_area = Listbox(self.main_window, width=42, height=32, selectbackground="Yellow")
        self.code_area.pack(side=LEFT)

        # Init control panel space
        self.control_frame = Frame(self.main_window)
        self.control_frame.pack(side=RIGHT)
        Label(self.control_frame, text="Control Panel", font=("TkDefaultFont", 32)).grid(row=0, column=0, pady=30)

        # Init space for panel to add new line to code area
        self.combo_frame = Frame(self.control_frame)
        self.combo_frame.grid(row=1, column=0)

        # Create combobox to set command type
        self.command_combo = ttk.Combobox(self.combo_frame, values=COMMANDS, width=7)
        self.command_combo.current(0)
        self.command_combo.grid(row=0, column=0, padx=5)

        # Create combobox to set first operand
        self.first_operand = ttk.Combobox(self.combo_frame, values=REGISTERS, width=7)
        self.first_operand.current(0)
        self.first_operand.grid(row=0, column=1, padx=5)

        # Create combobox to set second operand
        self.second_operand = ttk.Combobox(self.combo_frame, values=[*REGISTERS, "Number"], width=7)
        self.second_operand.current(0)
        self.second_operand.grid(row=0, column=2, padx=5)
        self.second_operand.bind("<<ComboboxSelected>>", self.value_changed)

        # Create entry field to set numeric operand
        self.num_entry = Entry(self.combo_frame, state="disabled", width=7)
        self.num_entry.grid(row=0, column=3, padx=5)

        # Init space for new line and delete line buttons
        self.button_frame = Frame(self.combo_frame)
        self.new_line_button = Button(self.button_frame, text="Add line", command=self.add_new_line).pack(pady=5)
        self.undo_button = Button(self.button_frame, text="Delete last line", command=self.delete_last_line).pack()
        self.button_frame.grid(row=0, column=4)

        # Init space for execute buttons and file handling buttons
        self.execute_frame = Frame(self.control_frame)
        self.execute_button = Button(self.execute_frame,
                                     text="Execute",
                                     command=self.execute_program).grid(row=0, column=0, padx=5)
        self.step_execute_button = Button(self.execute_frame,
                                          text="Step execute",
                                          command=self.make_step).grid(row=0, column=1, padx=5)
        self.save_to_file_button = Button(self.execute_frame,
                                          text="Save to file",
                                          command=self.save_to_file).grid(row=0, column=2, padx=5)
        self.load_from_file_button = Button(self.execute_frame,
                                            text="Load from file",
                                            command=self.load_from_file).grid(row=0, column=3, padx=5)
        self.execute_frame.grid(row=2, column=0, pady=50)

        # Init tree view for tracking registers' status
        self.status_tree = ttk.Treeview(self.control_frame)
        self.status_tree["columns"] = ("one", "two", "three")
        self.status_tree.column("#0", width=80, stretch=NO)
        self.status_tree.column("one", width=150, stretch=NO)
        self.status_tree.column("two", width=100, stretch=NO)
        self.status_tree.column("three", width=125, stretch=NO)

        self.status_tree.heading("#0", text="Register", anchor=W)
        self.status_tree.heading("one", text="BIN", anchor=W)
        self.status_tree.heading("two", text="DEC", anchor=W)
        self.status_tree.heading("three", text="HEX", anchor=W)

        # Create dictionary with register name as key and object storing it's current status as value
        self.register_dict = {}
        for register_name in ["A", "B", "C", "D"]:
            self.register_dict[register_name + "X"] = Register(0, f'{0:016b}')
            self.register_dict[register_name + "H"] = self.register_dict[register_name + "X"].h_register
            self.register_dict[register_name + "L"] = self.register_dict[register_name + "X"].l_register

        # Insert data into tree view
        status = ""
        for key in self.register_dict.keys():
            if key[1] == "X":
                status = self.status_tree.insert("", END, None, text=key,
                                                 values=(self.register_dict[key].bin_value,
                                                         self.register_dict[key].dec_value,
                                                         self.register_dict[key].hex_value))
            else:
                self.status_tree.insert(status, END, None, text=key,
                                        values=(self.register_dict[key].bin_value,
                                                self.register_dict[key].dec_value,
                                                self.register_dict[key].hex_value))

        self.status_tree.grid(row=3, column=0)

        # Current number of lines in code area
        self.line_counter = 1

        # Last executed line by step execution
        self.debug_counter = 0

    def value_changed(self, event=None):
        """
        If "Number" option is chosen as second operand, then set entry field state as normal, otherwise
        set as disabled.
        :param event: Second operand combobox value changed.
        """
        if self.second_operand.get() == "Number":
            self.num_entry.configure(state="normal")
        else:
            self.num_entry.configure(state="disabled")

    def add_new_line(self):
        """
        Insert new line into code area, using values in comboboxes.
        """
        # Get value from each combobox
        command = self.command_combo.get()
        operand1 = self.first_operand.get()
        operand2 = self.second_operand.get()

        # If second operand is "Number", then get value from entry field
        if operand2 == "Number":
            operand2 = self.num_entry.get()
            if not operand2.isdigit() or int(operand2) < 0 or int(operand2) > 255:
                return

        # Insert new line into code area
        self.code_area.insert(END, f"{self.line_counter} {command} {operand1}, {operand2}")
        self.line_counter += 1
        self.reset_registers()

    def delete_last_line(self):
        """
        Delete last line from code area.
        """
        if self.line_counter > 1:
            self.code_area.delete(END)
            self.line_counter -= 1
            self.reset_registers()

    def save_to_file(self):
        """
        Save code from code area to.txt file.
        """
        # Open browse window to ask for save directory
        filename = filedialog.asksaveasfilename(filetypes=[('Text', '*.txt')])

        # Save code to file
        with open(filename, 'w') as file:
            file.write("\n".join([" ".join(line.split(" ")[1:]) for line in self.code_area.get(0, END)]))

        # Show message box when code was successfully saved
        messagebox.showinfo("Information", "Successfully saved.")

    def load_from_file(self):
        """
        Load code to code area from .txt file.
        """
        # Open browse window to ask for file directory
        filename = filedialog.askopenfilename(filetypes=[('Text', '*.txt')])

        # Delete current code in code area
        self.code_area.delete(0, END)
        self.line_counter = 1

        # Read file and insert code into code area
        with open(filename, 'r') as file:
            for line in file:
                self.code_area.insert(END, str(self.line_counter) + " " + line.replace("\n", ""))
                self.line_counter += 1
        self.reset_registers()

        # Show message box when code was successfully loaded
        messagebox.showinfo("Information", f"Successfully loaded {filename}.")

    def execute_program(self):
        """
        Execute whole program at once.
        """
        self.reset_registers()
        while self.debug_counter < self.line_counter - 1:
            self.make_step()

    def make_step(self):
        """
        Handle single operation execute.
        """
        if self.line_counter == 1:
            return
        elif self.debug_counter == self.line_counter - 1:
            self.reset_registers()

        # Highlight currently executed line
        self.code_area.selection_clear(0, END)
        self.code_area.select_set(self.debug_counter)

        # Get command and operands from current line
        line = self.code_area.get(self.code_area.curselection())
        line = line.split(" ")
        command = line[1]
        operand1 = line[2].replace(",", "")
        operand2 = line[3]

        # Make right operation depending on command
        if command == "MOV":
            self.move_operation(operand1, operand2)
        elif command == "ADD":
            self.add_sub_operation(operand1, operand2, 1)
        elif command == "SUB":
            self.add_sub_operation(operand1, operand2, -1)

        self.update_tree(operand1)
        self.debug_counter += 1

    def move_operation(self, operand1, operand2):
        """
        Implementation of MOV command.
        :param operand1: first operand
        :param operand2: second operand
        """
        # If second operand is a number, then assign this value to the proper register,
        # otherwise assign value from another register.
        if operand2.isdigit() and 0 <= int(operand2) <= 255:
            self.register_dict[operand1].dec_value = int(operand2)
        else:
            self.register_dict[operand1].dec_value = self.register_dict[operand2].dec_value

        # Update binary and hexadecimal values
        self.register_dict[operand1].bin_value = f'{self.register_dict[operand1].dec_value:08b}'
        self.register_dict[operand1].hex_value = hex(self.register_dict[operand1].dec_value)

    def add_sub_operation(self, operand1, operand2, sign):
        """
        Implementation of ADD and SUB commands.
        :param operand1: first operand
        :param operand2: second operand
        :param sign: integer value, 1 for add command and -1 for sub command
        """
        # Update register's decimal value depending on second operand
        if operand2.isdigit() and 0 <= int(operand2) <= 255:
            self.register_dict[operand1].dec_value += sign * int(operand2)
        else:
            self.register_dict[operand1].dec_value += sign * self.register_dict[operand2].dec_value

        # Prevent exceeding the limit
        if self.register_dict[operand1].dec_value < 0:
            self.register_dict[operand1].dec_value = 0
        elif self.register_dict[operand1].dec_value > 255:
            self.register_dict[operand1].dec_value = 255

        # Update binary and hexadecimal values
        self.register_dict[operand1].bin_value = f'{self.register_dict[operand1].dec_value:08b}'
        self.register_dict[operand1].hex_value = hex(self.register_dict[operand1].dec_value)

    def reset_registers(self):
        """
        Set each register value to zero.
        """
        for register in REGISTERS:
            self.move_operation(register, "0")
            self.update_tree(register)

        self.debug_counter = 0

    def update_tree(self, operand1):
        """
        Update values in tree view.
        :param operand1: determines which nodes in tree must be changed
        """
        # Get main register name
        main_register = operand1.replace(operand1[-1], "X")

        # Update status of main register
        self.register_dict[main_register].bin_value = self.register_dict[main_register].h_register.bin_value \
                                                      + self.register_dict[main_register].l_register.bin_value
        self.register_dict[main_register].dec_value = int(self.register_dict[main_register].bin_value, 2)
        self.register_dict[main_register].hex_value = hex(self.register_dict[main_register].dec_value)

        # Update values tree using nodes indexing
        # Registers AX-CL are indexed as I001-I009 and registers DX-DL as I00A-I00C
        register_dict_key_list = list(self.register_dict.keys())
        for register in (operand1, main_register):
            position = "I00" + str(register_dict_key_list.index(register) + 1)
            if register_dict_key_list.index(operand1) + 1 >= 10:
                position = "I00" + str(hex(register_dict_key_list.index(register) + 1))[-1].upper()

            self.status_tree.item(position, values=(self.register_dict[register].bin_value,
                                                    self.register_dict[register].dec_value,
                                                    self.register_dict[register].hex_value))


if __name__ == "__main__":
    Simulator()
    mainloop()
