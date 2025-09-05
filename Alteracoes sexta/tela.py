import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import re
from datetime import datetime

# Configuração da conexão com o banco MySQL - ajuste seu usuário e senha aqui
config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'clinica'
}

# Função para conectar no banco
def conectar_bd():
    return mysql.connector.connect(**config)

# Login veterinário (fixo para exemplo)
veterinario_user = "vet"
veterinario_pass = "1234"

# ------------------ ABA VETERINÁRIO ----------------------

def tentar_login_vet():
    user = entry_login.get()
    passwd = entry_senha.get()
    if user == veterinario_user and passwd == veterinario_pass:
        frame_login_vet.pack_forget()
        frame_veterinario.pack(fill='both', expand=True)
        atualizar_combobox_vet_tutores()
    else:
        messagebox.showerror("Erro", "Usuário ou senha inválidos.")

def atualizar_combobox_vet_tutores():
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT Nome FROM Tutor")
        tutores = [row[0] for row in cursor.fetchall()]
        combo_vet_tutores['values'] = tutores
        combo_vet_pets.set('')
        combo_vet_pets['values'] = []
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao buscar tutores: {e}")

def atualizar_pets_por_tutor(event=None):
    nome_tutor = combo_vet_tutores.get()
    if not nome_tutor:
        combo_vet_pets['values'] = []
        return
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT CPF FROM Tutor WHERE Nome = %s", (nome_tutor,))
        resultado = cursor.fetchone()
        if resultado:
            cpf = resultado[0]
            cursor.execute("SELECT nome FROM Pet WHERE cpfTutor = %s", (cpf,))
            pets = [row[0] for row in cursor.fetchall()]
            combo_vet_pets['values'] = pets
        else:
            combo_vet_pets['values'] = []
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao buscar pets: {e}")

def enviar_relatorio():
    nome_tutor = combo_vet_tutores.get()
    nome_pet = combo_vet_pets.get()
    relatorio = text_relatorio.get("1.0", tk.END).strip()

    if not nome_tutor or not nome_pet or not relatorio:
        messagebox.showwarning("Aviso", "Selecione tutor, pet e escreva o relatório.")
        return

    try:
        conn = conectar_bd()
        cursor = conn.cursor()

        # Obter idPet
        cursor.execute("SELECT idPet FROM Pet WHERE nome = %s", (nome_pet,))
        pet_res = cursor.fetchone()
        if not pet_res:
            messagebox.showerror("Erro", "Pet não encontrado.")
            cursor.close()
            conn.close()
            return
        idPet = pet_res[0]

        # Obter idVeterinario pelo nome fixo do login veterinário
        cursor.execute("SELECT idVeterinario FROM Veterinario WHERE nome = %s", (veterinario_user,))
        vet_res = cursor.fetchone()
        if not vet_res:
            # Se não existir, cria veterinário genérico com nome do usuário e especialidade "Generalista"
            cursor.execute("INSERT INTO Veterinario (nome, especialidade) VALUES (%s, %s)", (veterinario_user, "Generalista"))
            conn.commit()
            cursor.execute("SELECT idVeterinario FROM Veterinario WHERE nome = %s", (veterinario_user,))
            vet_res = cursor.fetchone()
        idVet = vet_res[0]

        # Inserir consulta com data atual
        hoje = datetime.today().date()
        motivo = "Relatório via Veterinário"
        cursor.execute(
            "INSERT INTO Consulta (dataConsulta, motivoConsulta, idPet, idVeterinario, relatorio) VALUES (%s, %s, %s, %s, %s)",
            (hoje, motivo, idPet, idVet, relatorio)
        )
        conn.commit()
        messagebox.showinfo("Sucesso", "Relatório enviado e consulta registrada!")

        text_relatorio.delete("1.0", tk.END)
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao enviar relatório: {e}")

# ------------------ VALIDAÇÕES ---------------------------

def validar_data(data):
    padrao = r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}$"
    return re.match(padrao, data) is not None

def validar_cpf(cpf):
    return cpf.isdigit() and len(cpf) == 11

def validar_string(texto):
    return all(char.isalpha() or char.isspace() for char in texto)

def validar_telefone(telefone):
    return telefone.isdigit()

# ------------------ CADASTROS -----------------------------

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

    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Tutor (CPF, Nome, Email, Endereco, Telefone) VALUES (%s, %s, %s, %s, %s)",
                       (cpf, nome, email, endereco, telefone))
        conn.commit()
        messagebox.showinfo("Sucesso", f"Cliente {nome} cadastrado com sucesso!")
        cursor.close()
        conn.close()

        entry_cpf_cliente.delete(0, tk.END)
        entry_nome_cliente.delete(0, tk.END)
        entry_endereco.delete(0, tk.END)
        entry_telefone.delete(0, tk.END)
        entry_email.delete(0, tk.END)

        atualizar_combobox_clientes()
        atualizar_combobox_vet_tutores()
    except mysql.connector.IntegrityError:
        messagebox.showerror("Erro", "CPF já cadastrado!")
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao cadastrar cliente: {e}")

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
    # Validar nascimento no formato dd/mm/aaaa e converter para aaaa-mm-dd
    if not validar_data(nascimento):
        messagebox.showerror("Erro", "Data de nascimento inválida! Use dd/mm/aaaa.")
        return

    nascimento_formatado = datetime.strptime(nascimento, "%d/%m/%Y").strftime("%Y-%m-%d")

    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Pet (cpfTutor, dataNascimento, tipo, nome) VALUES (%s, %s, %s, %s)",
                       (cpf, nascimento_formatado, especie, nome))
        conn.commit()
        messagebox.showinfo("Sucesso", f"Pet '{nome}' cadastrado com sucesso para o cliente {nome_cliente}!")
        cursor.close()
        conn.close()

        entry_nome_pet.delete(0, tk.END)
        entry_especie_pet.delete(0, tk.END)
        entry_nascimento_pet.delete(0, tk.END)

        atualizar_combobox_pets()
        atualizar_combobox_vet_tutores()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao cadastrar pet: {e}")

def cadastrar_consulta():
    nome_cliente = combo_clientes_consulta.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    pet_nome = combo_pets_consulta.get()
    especialidade = combo_especialidade.get()
    motivo = entry_motivo_consulta.get()

    if not cpf or not pet_nome or not especialidade or not motivo:
        messagebox.showerror("Erro", "Preencha todos os campos corretamente.")
        return

    try:
        conn = conectar_bd()
        cursor = conn.cursor()

        # Obter idPet
        cursor.execute("SELECT idPet FROM Pet WHERE nome = %s AND cpfTutor = %s", (pet_nome, cpf))
        pet_res = cursor.fetchone()
        if not pet_res:
            messagebox.showerror("Erro", "Pet não encontrado para o tutor selecionado.")
            cursor.close()
            conn.close()
            return
        idPet = pet_res[0]

        # Obter idVeterinario pela especialidade
        cursor.execute("SELECT idVeterinario, nome FROM Veterinario WHERE especialidade = %s LIMIT 1", (especialidade,))
        vet_res = cursor.fetchone()
        if not vet_res:
            messagebox.showerror("Erro", "Nenhum veterinário encontrado para essa especialidade.")
            cursor.close()
            conn.close()
            return
        idVet, nomeVet = vet_res

        hoje = datetime.today().date()

        cursor.execute(
            "INSERT INTO Consulta (dataConsulta, motivoConsulta, idPet, idVeterinario, relatorio) VALUES (%s, %s, %s, %s, %s)",
            (hoje, motivo, idPet, idVet, "")
        )
        conn.commit()
        messagebox.showinfo("Sucesso", f"Consulta registrada com o veterinário {nomeVet}.")

        entry_motivo_consulta.delete(0, tk.END)
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao cadastrar consulta: {e}")

# ------------------ FUNÇÕES AUXILIARES --------------------

def obter_cpf_por_nome(nome):
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT CPF FROM Tutor WHERE Nome = %s", (nome,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        if resultado:
            return resultado[0]
        return None
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao buscar CPF: {e}")
        return None

def atualizar_combobox_clientes():
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT Nome FROM Tutor")
        nomes = [row[0] for row in cursor.fetchall()]
        combo_clientes['values'] = nomes
        combo_clientes_consulta['values'] = nomes
        cursor.close()
        conn.close()
        atualizar_combobox_pets()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar clientes: {e}")

def atualizar_combobox_pets(event=None):
    nome_cliente = combo_clientes_consulta.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    if not cpf:
        combo_pets_consulta['values'] = []
        return
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM Pet WHERE cpfTutor = %s", (cpf,))
        nomes_pets = [row[0] for row in cursor.fetchall()]
        combo_pets_consulta['values'] = nomes_pets
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar pets: {e}")

def atualizar_listagem():
    listbox_listagem.delete(0, tk.END)
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.Nome, t.CPF, p.nome, p.tipo, DATE_FORMAT(p.dataNascimento, '%d/%m/%Y')
            FROM Tutor t
            LEFT JOIN Pet p ON t.CPF = p.cpfTutor
            ORDER BY t.Nome, p.nome
        """)
        tutors_pets = cursor.fetchall()

        # Monta dicionário para consultas
        cursor.execute("""
            SELECT c.idConsulta, DATE_FORMAT(c.dataConsulta, '%d/%m/%Y'), c.motivoConsulta, c.relatorio, p.nome, t.Nome, v.nome, v.especialidade
            FROM Consulta c
            JOIN Pet p ON c.idPet = p.idPet
            JOIN Tutor t ON p.cpfTutor = t.CPF
            JOIN Veterinario v ON c.idVeterinario = v.idVeterinario
            ORDER BY c.dataConsulta DESC
        """)
        consultas = cursor.fetchall()

        consultas_por_pet = {}
        for c in consultas:
            pet_nome = c[4]
            consultas_por_pet.setdefault(pet_nome, []).append(c)

        for tutor in tutors_pets:
            nome_tutor, cpf, nome_pet, especie, nascimento = tutor
            if nome_pet is None:
                linha = f"Tutor: {nome_tutor} | CPF: {cpf} | Sem pets cadastrados"
                listbox_listagem.insert(tk.END, linha)
            else:
                linha = f"Tutor: {nome_tutor} | CPF: {cpf} | Pet: {nome_pet} | Espécie: {especie} | Nascimento: {nascimento}"
                listbox_listagem.insert(tk.END, linha)
                if nome_pet in consultas_por_pet:
                    for c in consultas_por_pet[nome_pet]:
                        _, data_consulta, motivo_consulta, relatorio, _, _, nome_vet, especialidade = c
                        listbox_listagem.insert(tk.END, f"    Consulta: {data_consulta} - Motivo: {motivo_consulta} - Veterinário: {nome_vet} ({especialidade})")
                        if relatorio.strip():
                            listbox_listagem.insert(tk.END, f"        Relatório: {relatorio}")
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar listagem: {e}")

def atualizar_especialidades():
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT especialidade FROM Veterinario")
        especialidades = [row[0] for row in cursor.fetchall()]
        combo_especialidade['values'] = especialidades
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar especialidades: {e}")

def atualizar_profissional(event=None):
    especialidade = combo_especialidade.get()
    if not especialidade:
        entry_profissional.config(state='normal')
        entry_profissional.delete(0, tk.END)
        entry_profissional.config(state='readonly')
        return
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM Veterinario WHERE especialidade = %s LIMIT 1", (especialidade,))
        vet = cursor.fetchone()
        if vet:
            entry_profissional.config(state='normal')
            entry_profissional.delete(0, tk.END)
            entry_profissional.insert(0, vet[0])
            entry_profissional.config(state='readonly')
        else:
            entry_profissional.config(state='normal')
            entry_profissional.delete(0, tk.END)
            entry_profissional.config(state='readonly')
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar profissional: {e}")

# ------------------ INTERFACE GRÁFICA ----------------------

root = tk.Tk()
root.title("Clínica Veterinária")
root.geometry("900x600")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# Aba Cadastro de Cliente
frame_cliente = ttk.Frame(notebook)
notebook.add(frame_cliente, text="Cadastro de Cliente")

tk.Label(frame_cliente, text="CPF do Cliente (11 dígitos):").pack()
entry_cpf_cliente = tk.Entry(frame_cliente)
entry_cpf_cliente.pack()

tk.Label(frame_cliente, text="Nome:").pack()
entry_nome_cliente = tk.Entry(frame_cliente)
entry_nome_cliente.pack()

tk.Label(frame_cliente, text="Endereço:").pack()
entry_endereco = tk.Entry(frame_cliente)
entry_endereco.pack()

tk.Label(frame_cliente, text="Telefone:").pack()
entry_telefone = tk.Entry(frame_cliente)
entry_telefone.pack()

tk.Label(frame_cliente, text="Email:").pack()
entry_email = tk.Entry(frame_cliente)
entry_email.pack()

btn_cadastrar_cliente = tk.Button(frame_cliente, text="Cadastrar Cliente", command=cadastrar_cliente)
btn_cadastrar_cliente.pack(pady=5)

# Aba Cadastro de Pet
frame_pet = ttk.Frame(notebook)
notebook.add(frame_pet, text="Cadastro de Pet")

tk.Label(frame_pet, text="Selecione Cliente:").pack()
combo_clientes = ttk.Combobox(frame_pet, state="readonly")
combo_clientes.pack()

tk.Label(frame_pet, text="Nome do Pet:").pack()
entry_nome_pet = tk.Entry(frame_pet)
entry_nome_pet.pack()

tk.Label(frame_pet, text="Espécie:").pack()
entry_especie_pet = tk.Entry(frame_pet)
entry_especie_pet.pack()

tk.Label(frame_pet, text="Data de Nascimento (dd/mm/aaaa):").pack()
entry_nascimento_pet = tk.Entry(frame_pet)
entry_nascimento_pet.pack()

btn_cadastrar_pet = tk.Button(frame_pet, text="Cadastrar Pet", command=cadastrar_pet)
btn_cadastrar_pet.pack(pady=5)

# Aba Consultas
frame_consulta = ttk.Frame(notebook)
notebook.add(frame_consulta, text="Consultas")

tk.Label(frame_consulta, text="Selecione Cliente:").pack()
combo_clientes_consulta = ttk.Combobox(frame_consulta, state="readonly")
combo_clientes_consulta.pack()
combo_clientes_consulta.bind("<<ComboboxSelected>>", atualizar_combobox_pets)

tk.Label(frame_consulta, text="Selecione Pet:").pack()
combo_pets_consulta = ttk.Combobox(frame_consulta, state="readonly")
combo_pets_consulta.pack()

tk.Label(frame_consulta, text="Especialidade do Veterinário:").pack()
combo_especialidade = ttk.Combobox(frame_consulta, state="readonly")
combo_especialidade.pack()
combo_especialidade.bind("<<ComboboxSelected>>", atualizar_profissional)

tk.Label(frame_consulta, text="Profissional:").pack()
entry_profissional = tk.Entry(frame_consulta, state='readonly')
entry_profissional.pack()

tk.Label(frame_consulta, text="Motivo da Consulta:").pack()
entry_motivo_consulta = tk.Entry(frame_consulta)
entry_motivo_consulta.pack()

btn_cadastrar_consulta = tk.Button(frame_consulta, text="Registrar Consulta", command=cadastrar_consulta)
btn_cadastrar_consulta.pack(pady=5)

# Aba Listagem
frame_listagem = ttk.Frame(notebook)
notebook.add(frame_listagem, text="Listagem")

listbox_listagem = tk.Listbox(frame_listagem)
listbox_listagem.pack(fill='both', expand=True)

btn_atualizar_listagem = tk.Button(frame_listagem, text="Atualizar Listagem", command=atualizar_listagem)
btn_atualizar_listagem.pack(pady=5)

# Aba Veterinário com login simples
frame_vet = ttk.Frame(notebook)
notebook.add(frame_vet, text="Veterinário")

frame_login_vet = ttk.Frame(frame_vet)
frame_login_vet.pack(fill='both', expand=True)

tk.Label(frame_login_vet, text="Login Veterinário").pack(pady=5)
entry_login = tk.Entry(frame_login_vet)
entry_login.pack(pady=5)

tk.Label(frame_login_vet, text="Senha").pack(pady=5)
entry_senha = tk.Entry(frame_login_vet, show="*")
entry_senha.pack(pady=5)

btn_login_vet = tk.Button(frame_login_vet, text="Entrar", command=tentar_login_vet)
btn_login_vet.pack(pady=5)

frame_veterinario = ttk.Frame(frame_vet)

tk.Label(frame_veterinario, text="Selecione Tutor:").pack()
combo_vet_tutores = ttk.Combobox(frame_veterinario, state='readonly')
combo_vet_tutores.pack()
combo_vet_tutores.bind("<<ComboboxSelected>>", atualizar_pets_por_tutor)

tk.Label(frame_veterinario, text="Selecione Pet:").pack()
combo_vet_pets = ttk.Combobox(frame_veterinario, state='readonly')
combo_vet_pets.pack()

tk.Label(frame_veterinario, text="Relatório:").pack()
text_relatorio = tk.Text(frame_veterinario, height=10)
text_relatorio.pack()

btn_enviar_relatorio = tk.Button(frame_veterinario, text="Enviar Relatório", command=enviar_relatorio)
btn_enviar_relatorio.pack(pady=5)

# Atualizações iniciais
atualizar_combobox_clientes()
atualizar_especialidades()

root.mainloop()
