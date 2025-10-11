from dataclasses import dataclass

@dataclass(frozen=True)
class ListaDeEmails:
    ederson = "ederson.duarte@minhabiblioteca.com.br"
    stephanie = "stephanie.souza@minhabiblioteca.com.br"
    victor = "victor.saade@minhabiblioteca.com.br"
    marcel = "marcel.sousa@minhabiblioteca.com.br"

__all__ = ["ListaDeEmails"]