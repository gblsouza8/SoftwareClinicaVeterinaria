import tkinter as tk
from tkinter import ttk, messagebox
import re

# Banco de dados em memória
clientes = {}  # CPF como chave
pets = {}      # CPF como chave, cada CPF pode ter lista de pets

# Validações

def validar_data(data):
    padrao = r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$"
    return re.match(padrao, data) is not None

def validar_cpf(cpf):
    return cpf.isdigit() and len(cpf) == 11

def validar_string(texto):
    return all(char.isalpha() or char.isspace() for char in texto)

def validar_telefone(telefone):
    return telefone.isdigit()

# Cadastro de cliente
def cadastrar_cliente():
    cpf = entry_cpf_cliente.get()
    nome = entry_nome_cliente.get()
    endereco = entry_endereco.get()
    telefone = entry_telefone.get()
    email = entry_email.get()

    if not validar_cpf(cpf):
        messagebox.showerror("Erro", "CPF inválido! Deve conter exatamente 11 números.")
        return
    if not validar_string(nome):
        messagebox.showerror("Erro", "Nome deve conter apenas letras.")
        return
    if not validar_string(endereco):
        messagebox.showerror("Erro", "Endereço deve conter apenas letras.")
        return
    if not validar_telefone(telefone):
        messagebox.showerror("Erro", "Telefone deve conter apenas números.")
        return

    clientes[cpf] = {"nome": nome, "endereco": endereco, "telefone": telefone, "email": email}
    messagebox.showinfo("Sucesso", f"Cliente {nome} cadastrado com sucesso!")
    entry_cpf_cliente.delete(0, tk.END)
    entry_nome_cliente.delete(0, tk.END)
    entry_endereco.delete(0, tk.END)
    entry_telefone.delete(0, tk.END)
    entry_email.delete(0, tk.END)

    atualizar_combobox_clientes()

# Cadastro de pets
def cadastrar_pet():
    nome_cliente = combo_clientes.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    nome = entry_nome_pet.get()
    especie = entry_especie_pet.get()
    nascimento = entry_nascimento_pet.get()

    if not cpf:
        messagebox.showerror("Erro", "Selecione um cliente existente.")
        return
    if not validar_string(nome):
        messagebox.showerror("Erro", "Nome do pet deve conter apenas letras.")
        return
    if not validar_string(especie):
        messagebox.showerror("Erro", "Espécie deve conter apenas letras.")
        return
    if not validar_data(nascimento):
        messagebox.showerror("Erro", "Data de nascimento inválida! Use dd/mm/aaaa.")
        return

    if cpf not in pets:
        pets[cpf] = []
    pets[cpf].append({"nome": nome, "especie": especie, "nascimento": nascimento, "consultas": []})
    messagebox.showinfo("Sucesso", f"Pet '{nome}' cadastrado com sucesso para o cliente {nome_cliente}!")

    entry_nome_pet.delete(0, tk.END)
    entry_especie_pet.delete(0, tk.END)
    entry_nascimento_pet.delete(0, tk.END)

# Cadastro de consultas
def cadastrar_consulta():
    nome_cliente = combo_clientes_consulta.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    pet_index = combo_pets_consulta.current()
    data = entry_data_consulta.get()
    motivo = entry_motivo_consulta.get()
    profissional = entry_profissional.get()
    especialidade = entry_especialidade.get()

    if not cpf or pet_index == -1:
        messagebox.showerror("Erro", "Selecione cliente e pet para cadastrar a consulta.")
        return
    if not validar_data(data):
        messagebox.showerror("Erro", "Data inválida! Use dd/mm/aaaa.")
        return

    pets[cpf][pet_index]['consultas'].append({"data": data, "motivo": motivo, "profissional": profissional, "especialidade": especialidade})
    messagebox.showinfo("Sucesso", "Consulta cadastrada com sucesso!")

    entry_data_consulta.delete(0, tk.END)
    entry_motivo_consulta.delete(0, tk.END)
    entry_profissional.delete(0, tk.END)
    entry_especialidade.delete(0, tk.END)

    atualizar_listagem()

# Funções auxiliares
def obter_cpf_por_nome(nome):
    for cpf, dados in clientes.items():
        if dados['nome'] == nome:
            return cpf
    return None

def atualizar_combobox_clientes():
    nomes = [dados['nome'] for dados in clientes.values()]
    combo_clientes['values'] = nomes
    combo_clientes_consulta['values'] = nomes
    atualizar_combobox_pets()

def atualizar_combobox_pets(event=None):
    nome_cliente = combo_clientes_consulta.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    if cpf in pets:
        nomes_pets = [pet['nome'] for pet in pets[cpf]]
        combo_pets_consulta['values'] = nomes_pets
    else:
        combo_pets_consulta['values'] = []

def atualizar_listagem():
    listbox_listagem.delete(0, tk.END)
    for cpf, lista_pets in pets.items():
        for pet in lista_pets:
            linha = f"Cliente: {clientes[cpf]['nome']} | CPF: {cpf} | Pet: {pet['nome']} | Espécie: {pet['especie']} | Nascimento: {pet['nascimento']}"
            listbox_listagem.insert(tk.END, linha)
            for c in pet['consultas']:
                listbox_listagem.insert(tk.END, f"    Consulta: {c['data']} - Motivo: {c['motivo']} - Profissional: {c['profissional']} - Especialidade: {c['especialidade']}")

# Interface gráfica
root = tk.Tk()
root.title("Clínica Veterinária")
root.geometry("800x550")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Aba Cadastro de Cliente
frame_cliente = ttk.Frame(notebook)
notebook.add(frame_cliente, text="Cadastro de Cliente")

label_cpf_cliente = tk.Label(frame_cliente, text="CPF do Cliente (11 dígitos):")
label_cpf_cliente.pack()
entry_cpf_cliente = tk.Entry(frame_cliente)
entry_cpf_cliente.pack()

label_nome_cliente = tk.Label(frame_cliente, text="Nome:")
label_nome_cliente.pack()
entry_nome_cliente = tk.Entry(frame_cliente)
entry_nome_cliente.pack()

label_endereco = tk.Label(frame_cliente, text="Endereço:")
label_endereco.pack()
entry_endereco = tk.Entry(frame_cliente)
entry_endereco.pack()

label_telefone = tk.Label(frame_cliente, text="Telefone:")
label_telefone.pack()
entry_telefone = tk.Entry(frame_cliente)
entry_telefone.pack()

label_email = tk.Label(frame_cliente, text="Email:")
label_email.pack()
entry_email = tk.Entry(frame_cliente)
entry_email.pack()

btn_cadastrar_cliente = tk.Button(frame_cliente, text="Cadastrar Cliente", command=cadastrar_cliente)
btn_cadastrar_cliente.pack()

# Aba Cadastro de Pet
frame_pet = ttk.Frame(notebook)
notebook.add(frame_pet, text="Cadastro de Pet")

label_cliente_pet = tk.Label(frame_pet, text="Selecione Cliente:")
label_cliente_pet.pack()
combo_clientes = ttk.Combobox(frame_pet, state="readonly")
combo_clientes.pack()

label_nome_pet = tk.Label(frame_pet, text="Nome do Pet:")
label_nome_pet.pack()
entry_nome_pet = tk.Entry(frame_pet)
entry_nome_pet.pack()

label_especie_pet = tk.Label(frame_pet, text="Espécie:")
label_especie_pet.pack()
entry_especie_pet = tk.Entry(frame_pet)
entry_especie_pet.pack()

label_nascimento_pet = tk.Label(frame_pet, text="Data de Nascimento (dd/mm/aaaa):")
label_nascimento_pet.pack()
entry_nascimento_pet = tk.Entry(frame_pet)
entry_nascimento_pet.pack()

btn_cadastrar_pet = tk.Button(frame_pet, text="Cadastrar Pet", command=cadastrar_pet)
btn_cadastrar_pet.pack()

# Aba Consultas
frame_consulta = ttk.Frame(notebook)
notebook.add(frame_consulta, text="Consultas")

label_cliente_consulta = tk.Label(frame_consulta, text="Selecione Cliente:")
label_cliente_consulta.pack()
combo_clientes_consulta = ttk.Combobox(frame_consulta, state="readonly")
combo_clientes_consulta.pack()
combo_clientes_consulta.bind("<<ComboboxSelected>>", atualizar_combobox_pets)

label_pet_consulta = tk.Label(frame_consulta, text="Selecione Pet:")
label_pet_consulta.pack()
combo_pets_consulta = ttk.Combobox(frame_consulta, state="readonly")
combo_pets_consulta.pack()

label_data_consulta = tk.Label(frame_consulta, text="Data da Consulta (dd/mm/aaaa):")
label_data_consulta.pack()
entry_data_consulta = tk.Entry(frame_consulta)
entry_data_consulta.pack()

label_motivo_consulta = tk.Label(frame_consulta, text="Motivo:")
label_motivo_consulta.pack()
entry_motivo_consulta = tk.Entry(frame_consulta)
entry_motivo_consulta.pack()

label_profissional = tk.Label(frame_consulta, text="Profissional Encaminhado:")
label_profissional.pack()
entry_profissional = tk.Entry(frame_consulta)
entry_profissional.pack()

label_especialidade = tk.Label(frame_consulta, text="Especialidade do Profissional:")
label_especialidade.pack()
entry_especialidade = tk.Entry(frame_consulta)
entry_especialidade.pack()

btn_cadastrar_consulta = tk.Button(frame_consulta, text="Cadastrar Consulta", command=cadastrar_consulta)
btn_cadastrar_consulta.pack()

# Aba Listagem
frame_listagem = ttk.Frame(notebook)
notebook.add(frame_listagem, text="Listagem")

listbox_listagem = tk.Listbox(frame_listagem, width=100, height=25)
listbox_listagem.pack()

root.mainloop()
