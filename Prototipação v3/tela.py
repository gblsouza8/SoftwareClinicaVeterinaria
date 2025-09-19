import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import re
from datetime import datetime

root = tk.Tk()

frame_consulta = ttk.Frame(root)
frame_consulta.pack()

config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'clinica'
}

# Função para conectar no banco
def conectar_bd():
    try:
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {err}")
        return None

# Login veterinário
veterinario_user = "admin"
veterinario_pass = "1234"

# Aba veterinário
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
    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Nome FROM Tutor")
        tutores = [row[0] for row in cursor.fetchall()]
        combo_vet_tutores['values'] = tutores
        combo_vet_pets.set('')
        combo_vet_pets['values'] = []
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao buscar tutores: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def atualizar_pets_por_tutor(event=None):
    nome_tutor = combo_vet_tutores.get()
    if not nome_tutor:
        combo_vet_pets['values'] = []
        return
    conn = conectar_bd()
    if not conn:
        return
    try:
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
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao buscar pets: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def enviar_relatorio():
    nome_tutor = combo_vet_tutores.get()
    nome_pet = combo_vet_pets.get()
    relatorio = text_relatorio.get("1.0", tk.END).strip()

    if not nome_tutor or not nome_pet or not relatorio:
        messagebox.showwarning("Aviso", "Selecione tutor, pet e escreva o relatório.")
        return

    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()

        # Obter idPet
        cursor.execute("SELECT idPet FROM Pet WHERE nome = %s", (nome_pet,))
        pet_res = cursor.fetchone()
        if not pet_res:
            messagebox.showerror("Erro", "Pet não encontrado.")
            return
        idPet = pet_res[0]

        # Encontrar o idConsulta mais alto para o pet (consultas mais recentes)
        cursor.execute(
            "SELECT idConsulta FROM Consulta WHERE idPet = %s ORDER BY idConsulta DESC LIMIT 1",
            (idPet,)
        )
        consulta_res = cursor.fetchone()

        if not consulta_res:
            messagebox.showerror("Erro", "Não há consultas anteriores para este pet.")
            return

        idConsulta = consulta_res[0]

        # Atualizar a consulta com o novo relatório
        cursor.execute(
            "UPDATE Consulta SET relatorio = %s WHERE idConsulta = %s",
            (relatorio, idConsulta)
        )
        conn.commit()
        messagebox.showinfo("Sucesso", "Relatório atualizado com sucesso na consulta mais recente!")

        text_relatorio.delete("1.0", tk.END)

    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao enviar relatório: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

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

def validar_endereco(endereco):
    return len(endereco.strip()) > 0


# ------------------ CADASTROS -----------------------------

def cadastrar_cliente():
    cpf = entry_cpf_cliente.get().strip()
    nome = entry_nome_cliente.get().strip()
    endereco = entry_endereco.get().strip()
    telefone = entry_telefone.get().strip()
    email = entry_email.get().strip()

    if not cpf or not nome:
        messagebox.showwarning("Aviso", "CPF e Nome são obrigatórios.")
        return

    conn = conectar_bd()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Tutor (CPF, Nome, Endereco, Telefone, Email) VALUES (%s, %s, %s, %s, %s)",
            (cpf, nome, endereco, telefone, email)
        )
        conn.commit()
        messagebox.showinfo("Sucesso", "Cliente cadastrado com sucesso!")

        # Limpa campos
        entry_cpf_cliente.delete(0, tk.END)
        entry_nome_cliente.delete(0, tk.END)
        entry_endereco.delete(0, tk.END)
        entry_telefone.delete(0, tk.END)
        entry_email.delete(0, tk.END)

        # Atualiza comboboxes
        atualizar_combobox_clientes()
        atualizar_combobox_vet_tutores()

    except mysql.connector.IntegrityError:
        messagebox.showerror("Erro", "CPF já cadastrado!")
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao cadastrar cliente: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


def cadastrar_pet():
    nome_cliente = combo_clientes.get()
    if not nome_cliente:
        messagebox.showerror("Erro", "Selecione um cliente existente.")
        return

    cpf = obter_cpf_por_nome(nome_cliente)
    if not cpf:
        messagebox.showerror("Erro", "Não foi possível obter CPF do cliente selecionado.")
        return

    nome = entry_nome_pet.get().strip()
    especie = entry_especie_pet.get().strip()
    nascimento = entry_nascimento_pet.get().strip()

    if not nome:
        messagebox.showerror("Erro", "Nome do pet não pode estar vazio.")
        return
    if not validar_string(especie):
        messagebox.showerror("Erro", "Espécie deve conter apenas letras.")
        return
    if not validar_data(nascimento):
        messagebox.showerror("Erro", "Data de nascimento inválida! Use dd/mm/aaaa.")
        return

    try:
        nascimento_formatado = datetime.strptime(nascimento, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Erro", 
                             "Formato de data inválido. Use dd/mm/aaaa.")
        return

    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Pet (cpfTutor, dataNascimento, tipo, nome) VALUES (%s, %s, %s, %s)",
            (cpf, nascimento_formatado, especie, nome)
        )
        conn.commit()
        messagebox.showinfo("Sucesso", f"Pet '{nome}' cadastrado com sucesso para o cliente {nome_cliente}!")

        # limpa campos do pet
        entry_nome_pet.delete(0, tk.END)
        entry_especie_pet.delete(0, tk.END)
        entry_nascimento_pet.delete(0, tk.END)

        atualizar_combobox_pets(event=None)
        atualizar_combobox_vet_tutores()

    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao cadastrar pet: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def atualizar_combobox_pets(event=None):
    global combo_pets          # garante que a variável global é usada
    tutor = combo_clientes.get()
    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome FROM Pet "
            "JOIN Tutor ON Pet.cpfTutor = Tutor.CPF "
            "WHERE Tutor.Nome = %s",
            (tutor,)
        )
        pets = [p[0] for p in cursor.fetchall()]
        combo_pets['values'] = pets
    finally:
        cursor.close()
        conn.close()



def cadastrar_consulta():
    nome_cliente = combo_clientes_consulta.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    pet_nome = combo_pets_consulta.get()
    especialidade = combo_especialidade.get()
    motivo = entry_motivo_consulta.get()

    if not cpf or not pet_nome or not especialidade or not motivo:
        messagebox.showerror("Erro", "Preencha todos os campos corretamente.")
        return

    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()

        # Obter idPet
        cursor.execute("SELECT idPet FROM Pet WHERE nome = %s AND cpfTutor = %s", (pet_nome, cpf))
        pet_res = cursor.fetchone()
        if not pet_res:
            messagebox.showerror("Erro", "Pet não encontrado para o tutor selecionado.")
            return
        idPet = pet_res[0]

        # Obter idVeterinario pela especialidade
        cursor.execute("SELECT idVeterinario, nome FROM Veterinario WHERE especialidade = %s LIMIT 1", (especialidade,))
        vet_res = cursor.fetchone()
        if not vet_res:
            messagebox.showerror("Erro", "Nenhum veterinário encontrado para essa especialidade.")
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

    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao cadastrar consulta: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ------------------ FUNÇÕES AUXILIARES --------------------
def obter_cpf_por_nome(nome):
    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CPF FROM Tutor WHERE Nome = %s", (nome,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        return None
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao buscar CPF: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

combo_clientes = ttk.Combobox(frame_consulta, state="readonly")
combo_clientes.pack()

def atualizar_combobox_pets_cadastro(event=None):
    # código para atualizar a lista de pets
    print("Atualizando pets...")

combo_clientes.bind("<<ComboboxSelected>>", atualizar_combobox_pets_cadastro)





def atualizar_combobox_clientes():
    conn = conectar_bd()
    if not conn:
        return
    try:
        combo_clientes.bind("<<ComboboxSelected>>", atualizar_combobox_pets_cadastro)

        cursor = conn.cursor()
        cursor.execute("SELECT Nome FROM Tutor")
        nomes = [row[0] for row in cursor.fetchall()]
        combo_clientes['values'] = nomes
        combo_clientes_consulta['values'] = nomes
        

        
        
        atualizar_combobox_pets()
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar clientes: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def atualizar_combobox_pets(event=None):
    nome_cliente = combo_clientes_consulta.get()
    cpf = obter_cpf_por_nome(nome_cliente)
    if not cpf:
        combo_pets_consulta['values'] = []
        return
    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM Pet WHERE cpfTutor = %s", (cpf,))
        nomes_pets = [row[0] for row in cursor.fetchall()]
        combo_pets_consulta['values'] = nomes_pets
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar pets: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def criar_aba_consulta(notebook):
    frame_consulta = ttk.Frame(notebook)
    notebook.add(frame_consulta, text="Consultas")
    ...


def atualizar_listagem():
    # 1. Limpa todas as linhas existentes
    for item in tree.get_children():
        tree.delete(item)

    conn = conectar_bd()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.Nome, t.CPF, p.nome, p.tipo,
                   DATE_FORMAT(p.dataNascimento, '%d/%m/%Y')
            FROM Tutor t
            LEFT JOIN Pet p ON t.CPF = p.cpfTutor
            ORDER BY t.Nome, p.nome
        """)
        for nome_tutor, cpf, nome_pet, especie, nascimento in cursor.fetchall():
            tree.insert(
                "",
                tk.END,
                values=(nome_tutor,
                        cpf,
                        nome_pet if nome_pet else "-",
                        especie if especie else "-",
                        nascimento if nascimento else "-")
            )
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar listagem: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# criação na interface, antes do botão de consulta
# criar a aba antes
frame_consulta = ttk.Frame(ttk.Notebook)
ttk.Notebook.add(frame_consulta, text="Consultas")

# criar combobox
combo_especialidade = ttk.Combobox(frame_consulta, state="readonly")
combo_especialidade.pack(pady=5)

def atualizar_especialidades():
    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT especialidade FROM Veterinario")
        especialidades = [v[0] for v in cursor.fetchall()]
        combo_especialidade['values'] = especialidades
    finally:
        cursor.close()
        conn.close()





def atualizar_profissional(event=None):
    especialidade = combo_especialidade.get()
    if not especialidade:
        entry_profissional.config(state='normal')
        entry_profissional.delete(0, tk.END)
        entry_profissional.config(state='readonly')
        return
    conn = conectar_bd()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nome FROM Veterinario WHERE especialidade = %s LIMIT 1", (especialidade,))
        vet = cursor.fetchone()
        entry_profissional.config(state='normal')
        entry_profissional.delete(0, tk.END)
        if vet:
            entry_profissional.insert(0, vet[0])
        entry_profissional.config(state='readonly')
    except Exception as e:
        messagebox.showerror("Erro BD", f"Erro ao atualizar profissional: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ------------------ INTERFACE GRÁFICA ----------------------
root = tk.Tk()
root.title("Clínica Veterinária")
root.geometry("800x600")
root.configure(bg="#ecf0f1")

# Estilos ttk
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton",
                font=("Segoe UI", 10, "bold"),
                padding=8,
                relief="flat",
                background="#3498db",
                foreground="white")
style.map("TButton",
          background=[("active", "#2980b9")])
style.configure("TLabel",
                font=("Segoe UI", 10),
                background="#f4f6f7")
style.configure("TEntry",
                padding=5)
style.configure("TNotebook", background="#f4f6f7")
style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[12, 8])

# Notebook principal
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

style.configure("TNotebook", background="#f4f6f7")
style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[10, 5])


notebook.pack(fill="both", expand=True)  # sem padx, sem pady

# Aba Cadastro de Cliente
frame_cliente = ttk.Frame(notebook)
notebook.add(frame_cliente, text="Cadastro de Cliente")

tk.Label(
    frame_cliente, text="Cadastro de Cliente",
    font=("Segoe UI", 16, "bold"),
    bg="#f4f6f7", fg="#2c3e50"
).grid(row=0, column=0, columnspan=2, pady=20)

tk.Label(frame_cliente, text="CPF (11 dígitos):", bg="#f4f6f7").grid(row=1, column=0, sticky="e", padx=10, pady=8)
entry_cpf_cliente = ttk.Entry(frame_cliente, width=30)
entry_cpf_cliente.grid(row=1, column=1, pady=8)

tk.Label(frame_cliente, text="Nome:", bg="#f4f6f7").grid(row=2, column=0, sticky="e", padx=10, pady=8)
entry_nome_cliente = ttk.Entry(frame_cliente, width=30)
entry_nome_cliente.grid(row=2, column=1, pady=8)

tk.Label(frame_cliente, text="Endereço:", bg="#f4f6f7").grid(row=3, column=0, sticky="e", padx=10, pady=8)
entry_endereco = ttk.Entry(frame_cliente, width=30)
entry_endereco.grid(row=3, column=1, pady=8)

tk.Label(frame_cliente, text="Telefone:", bg="#f4f6f7").grid(row=4, column=0, sticky="e", padx=10, pady=8)
entry_telefone = ttk.Entry(frame_cliente, width=30)
entry_telefone.grid(row=4, column=1, pady=8)

tk.Label(frame_cliente, text="Email:", bg="#f4f6f7").grid(row=5, column=0, sticky="e", padx=10, pady=8)
entry_email = ttk.Entry(frame_cliente, width=30)
entry_email.grid(row=5, column=1, pady=8)

btn_cadastrar_cliente = ttk.Button(
    frame_cliente, text="Cadastrar Cliente", command=cadastrar_cliente
)
btn_cadastrar_cliente.grid(row=6, column=0, columnspan=2, pady=25)



# Aba Cadastro de Pet
frame_pet = ttk.Frame(notebook)
notebook.add(frame_pet, text="Cadastro de Pet")

tk.Label(frame_pet, text="Cadastro de Pet",
         font=("Segoe UI", 16, "bold"),
         bg="#f4f6f7", fg="#2c3e50").pack(pady=15)

tk.Label(frame_pet, text="Selecione Cliente:").pack()
combo_clientes = ttk.Combobox(frame_pet, state="readonly")
combo_clientes.pack(pady=5)

tk.Label(frame_pet, text="Nome do Pet:").pack()
entry_nome_pet = tk.Entry(frame_pet, width=25)
entry_nome_pet.pack(pady=5)

tk.Label(frame_pet, text="Espécie:").pack()
entry_especie_pet = tk.Entry(frame_pet, width=25)
entry_especie_pet.pack(pady=5)

tk.Label(frame_pet, text="Data de Nascimento (dd/mm/aaaa):").pack()
entry_nascimento_pet = tk.Entry(frame_pet, width=25)
entry_nascimento_pet.pack(pady=5)

btn_cadastrar_pet = ttk.Button(frame_pet, text="Cadastrar Pet", command=cadastrar_pet)
btn_cadastrar_pet.pack(pady=15)

# Aba Consultas
frame_consulta = ttk.Frame(notebook)
notebook.add(frame_consulta, text="Consultas")

tk.Label(frame_consulta, text="Consultas",
         font=("Segoe UI", 16, "bold"),
         bg="#f4f6f7", fg="#2c3e50").pack(pady=15)

tk.Label(frame_consulta, text="Selecione Cliente:").pack()
combo_clientes_consulta = ttk.Combobox(frame_consulta, state="readonly")
combo_clientes_consulta.pack(pady=5)

tk.Label(frame_consulta, text="Selecione Pet:").pack()
combo_pets_consulta = ttk.Combobox(frame_consulta, state="readonly")
combo_pets_consulta.pack(pady=5)

tk.Label(frame_consulta, text="Especialidade do Veterinário:").pack()
combo_especialidade = ttk.Combobox(frame_consulta, state="readonly")
combo_especialidade.pack(pady=5)

tk.Label(frame_consulta, text="Profissional:").pack()
entry_profissional = tk.Entry(frame_consulta, width=25, state="readonly")
entry_profissional.pack(pady=5)

tk.Label(frame_consulta, text="Motivo da Consulta:").pack()
entry_motivo_consulta = tk.Entry(frame_consulta, width=25)
entry_motivo_consulta.pack(pady=5)

btn_cadastrar_consulta = ttk.Button(frame_consulta, text="Registrar Consulta", command=cadastrar_consulta)
btn_cadastrar_consulta.pack(pady=15)
# Aba Listagem
frame_listagem = ttk.Frame(notebook)
notebook.add(frame_listagem, text="Listagem")

tk.Label(frame_listagem, text="Listagem Geral",
         font=("Segoe UI", 16, "bold"),
         bg="#f4f6f7", fg="#2c3e50").pack(pady=15)

tree = ttk.Treeview(frame_listagem, columns=("Tutor", "CPF", "Pet", "Espécie", "Nascimento"), show="headings")
tree.heading("Tutor", text="Tutor")
tree.heading("CPF", text="CPF")
tree.heading("Pet", text="Pet")
tree.heading("Espécie", text="Espécie")
tree.heading("Nascimento", text="Nascimento")
tree.pack(fill="both", expand=True, padx=10, pady=10)

btn_atualizar_listagem = ttk.Button(frame_listagem, text="Atualizar Listagem", command=atualizar_listagem)
btn_atualizar_listagem.pack(pady=10)
# Aba Veterinário com login simples
frame_vet = ttk.Frame(notebook)
notebook.add(frame_vet, text="Veterinário")

frame_login_vet = ttk.Frame(frame_vet)
frame_login_vet.pack(fill='both', expand=True)

tk.Label(frame_login_vet, text="Login Veterinário", font=('Helvetica', 12, 'bold')).pack(pady=10)
tk.Label(frame_login_vet, text="Usuário").pack(pady=(10, 0))
entry_login = tk.Entry(frame_login_vet, width=20)
entry_login.pack(pady=5, padx=10)

tk.Label(frame_login_vet, text="Senha").pack(pady=(10, 0))
entry_senha = tk.Entry(frame_login_vet, width=20, show="*")
entry_senha.pack(pady=5, padx=10)

btn_login_vet = ttk.Button(frame_login_vet, text="Entrar", command=tentar_login_vet)
btn_login_vet.pack(pady=10)

frame_veterinario = ttk.Frame(frame_vet)

tk.Label(frame_veterinario, text="Selecione Tutor:").pack(pady=(10, 0))
combo_vet_tutores = ttk.Combobox(frame_veterinario, state='readonly')
combo_vet_tutores.pack(pady=5, padx=10)
combo_vet_tutores.bind("<<ComboboxSelected>>", atualizar_pets_por_tutor)

tk.Label(frame_veterinario, text="Selecione Pet:").pack()
combo_vet_pets = ttk.Combobox(frame_veterinario, state='readonly')
combo_vet_pets.pack(pady=5, padx=10)

tk.Label(frame_veterinario, text="Relatório:").pack()
text_relatorio = tk.Text(frame_veterinario, height=10)
text_relatorio.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

btn_enviar_relatorio = ttk.Button(frame_veterinario, text="Enviar Relatório", command=enviar_relatorio)
btn_enviar_relatorio.pack(pady=10)

# Atualizações iniciais
atualizar_combobox_clientes()        # aba de consultas (clientes)
atualizar_combobox_vet_tutores()     # se usa tutores em outra aba
atualizar_especialidades()           # profissionais/especialidades

root.mainloop()