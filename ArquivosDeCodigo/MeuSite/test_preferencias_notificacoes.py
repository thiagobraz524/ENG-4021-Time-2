from django.test import TestCase
from django.urls import reverse

from banco_de_dados.models import PreferenciaNotificacao, Usuario


class TestesPreferenciasNotificacoes(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nome='Pessoa', email='preferencias@teste.com', senha='teste'
        )
        sessao = self.client.session
        sessao['usuario_id'] = self.usuario.id
        sessao.save()
        self.url = reverse('PreferenciasNotificacoes')

    def test_necessita_login(self):
        self.client.session.flush()
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)

    def test_primeiro_acesso_mostra_valores_padrao(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'name="lembrar_consultas" value="sim" checked')
        self.assertContains(resposta, '<option value="3" selected>')
        self.assertFalse(PreferenciaNotificacao.objects.exists())

    def test_salva_as_preferencias(self):
        resposta = self.client.post(self.url, {
            'lembrar_vacinas': 'sim',
            'antecedencia': '7',
            'email_contato': 'Contato@Teste.com',
        })
        self.assertContains(resposta, 'Preferências salvas com sucesso.')
        preferencia = PreferenciaNotificacao.objects.get(usuario=self.usuario)
        self.assertFalse(preferencia.lembrar_consultas)
        self.assertFalse(preferencia.lembrar_exames)
        self.assertTrue(preferencia.lembrar_vacinas)
        self.assertEqual(preferencia.antecedencia_dias, 7)
        self.assertEqual(preferencia.email_contato, 'contato@teste.com')

    def test_salvar_de_novo_atualiza_sem_duplicar(self):
        self.client.post(self.url, {'lembrar_exames': 'sim', 'antecedencia': '1'})
        self.client.post(self.url, {'lembrar_consultas': 'sim', 'antecedencia': '3'})
        self.assertEqual(PreferenciaNotificacao.objects.count(), 1)
        preferencia = PreferenciaNotificacao.objects.get(usuario=self.usuario)
        self.assertTrue(preferencia.lembrar_consultas)
        self.assertFalse(preferencia.lembrar_exames)
        self.assertEqual(preferencia.antecedencia_dias, 3)

    def test_tela_mostra_o_que_foi_salvo(self):
        self.client.post(self.url, {'lembrar_vacinas': 'sim', 'antecedencia': '1'})
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'name="lembrar_vacinas" value="sim" checked')
        self.assertNotContains(resposta, 'name="lembrar_consultas" value="sim" checked')
        self.assertContains(resposta, '<option value="1" selected>')

    def test_rejeita_antecedencia_invalida(self):
        resposta = self.client.post(self.url, {'antecedencia': '30'})
        self.assertContains(resposta, 'Escolha quando gostaria de ser avisado.')
        self.assertFalse(PreferenciaNotificacao.objects.exists())
