from abc import ABC, abstractmethod


class IView(ABC):
    @abstractmethod
    def show_error(self, msg: str): ...

    @abstractmethod
    def show_success(self, msg: str): ...

    @abstractmethod
    def display_menu(
        self,
        opcoes: list[str],
        mensagem="Selecione uma opção:",
        selecionar_todos=False,
        permitir_voltar=False,
    ): ...

    @abstractmethod
    def get_user_input(
        self,
        opcoes: list[str],
        selecionar_todos=False,
        permitir_voltar=False,
        multipla_escolha=False,
    ) -> list[str] | None: ...

    def show_processing_message(self, message: str): ...

    def show_message(self, message: str): ...
