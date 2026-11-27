from datetime import date

from django.test import TestCase
from django.urls import reverse

from banco_de_dados.models import HistoricoFamiliar, Perfil, Usuario


class TestesFamiliares(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nome='Pessoa', email='familiares@teste.com', senha='teste'
        )

    def entrar(self):
        sessao = self.client.session
        sessao['usuario_id'] = self.usuario.id
        sessao.save()

    def criar_perfil(self, usuario):
        return Perfil.objects.create(
            usuario=usuario, nome=usuario.nome,
            data_nascimento=date(1990, 1, 1), sexo='Feminino'
        )

    def test_sem_login_vai_para_a_tela_de_entrar(self):
        resposta = self.client.get(reverse('Familiares'))
        self.assertRedirects(resposta, reverse('Tela'))

    def test_sem_perfil_vai_para_o_perfil_de_saude(self):
        self.entrar()
        resposta = self.client.get(reverse('Familiares'))
        self.assertRedirects(resposta, reverse('PerfilSaude'))

    def test_mostra_somente_os_familiares_do_usuario(self):
        self.entrar()
        perfil = self.criar_perfil(self.usuario)
        HistoricoFamiliar.objects.create(perfil=perfil, parente='Mãe', doenca='Diabetes tipo 2',
                                         idade_diagnostico=50)
        outro = Usuario.objects.create(nome='Outro', email='outro-familiares@teste.com', senha='teste')
        HistoricoFamiliar.objects.create(perfil=self.criar_perfil(outro), parente='Pai',
                                         doenca='Doença de outra pessoa')

        resposta = self.client.get(reverse('Familiares'))
        self.assertContains(resposta, 'Diabetes tipo 2')
        self.assertContains(resposta, '50 anos')
        self.assertNotContains(resposta, 'Doença de outra pessoa')

    def test_idade_vazia_nao_mostra_none(self):
        self.entrar()
        perfil = self.criar_perfil(self.usuario)
        HistoricoFamiliar.objects.create(perfil=perfil, parente='Avô', doenca='Hipertensão')
        resposta = self.client.get(reverse('Familiares'))
        self.assertContains(resposta, 'Não informada')
        self.assertNotContains(resposta, 'None')
