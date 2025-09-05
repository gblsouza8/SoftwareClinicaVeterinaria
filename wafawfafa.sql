create database clinica;

use clinica;
create table Tutor (
	CPF VARCHAR(14) UNIQUE NOT NULL,
    Nome VARCHAR(100),
    Email VARCHAR(100),
    Endereco VARCHAR(100),
    Telefone VARCHAR(20)
);



create table Pet (
	idPet INT auto_increment,
    cpfTutor VARCHAR(14) not null,
    dataNascimento DATE,
    tipo VARCHAR(45),
    nome VARCHAR(45),
    PRIMARY KEY (idPet),
    FOREIGN KEY (cpfTutor) REFERENCES Tutor(CPF)
);


create table Veterinario (
	idVeterinario int auto_increment primary key,
    especialidade VARCHAR(45),
    nome VARCHAR(100)
);

create table Consulta (
	idConsulta int auto_increment primary key,
    dataConsulta DATE,
    motivoConsulta VARCHAR(100),
    idPet INT,
    idVeterinario INT,
    relatorio varchar(255),
    
    foreign key (idPet) references Pet (idPet),
    foreign key (idVeterinario) references Veterinario (idVeterinario)
);

INSERT INTO Veterinario (nome, especialidade) VALUES ('Dr. João', 'Cardiologia');


select * from tutor;

select * from pet;