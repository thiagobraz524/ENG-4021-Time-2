from django.test import TestCase
from django.urls import reverse

from banco_de_dados.models import Consentimento, Usuario


class TestesConsentimentoDados(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nome='Pessoa', email='consentimento@teste.com', senha='teste'
        )
        sessao = self.client.session
        sessao['usuario_id'] = self.usuario.id
        sessao.save()
        self.url = reverse('ConsentimentoDados')

    def test_necessita_login(self):
        self.client.session.flush()
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 302)

    def test_primeiro_acesso_mostra_pendente(self):
        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Você ainda não deu o seu consentimento.')
        self.assertContains(resposta, 'Confirmar consentimento')

    def test_aceitar_salva_com_data(self):
        self.client.post(self.url, {'aceitou_uso_dados': 'sim'})
        consentimento = Consentimento.objects.get(usuario=self.usuario)
        self.assertTrue(consentimento.aceitou_uso_dados)
        self.assertFalse(consentimento.aceitou_comunicacoes)
        self.assertIsNotNone(consentimento.data_consentimento)

        resposta = self.client.get(self.url)
        self.assertContains(resposta, 'Você aceitou o uso dos seus dados em')

    def test_atualizar_comunicacoes_mantem_a_data_do_aceite(self):
        self.client.post(self.url, {'aceitou_uso_dados': 'sim'})
        data_original = Consentimento.objects.get(usuario=self.usuario).data_consentimento

        self.client.post(self.url, {'aceitou_uso_dados': 'sim', 'aceitou_comunicacoes': 'sim'})
        consentimento = Consentimento.objects.get(usuario=self.usuario)
        self.assertTrue(consentimento.aceitou_comunicacoes)
        self.assertEqual(consentimento.data_consentimento, data_original)
        self.assertEqual(Consentimento.objects.count(), 1)

    def test_retirar_consentimento(self):
        self.client.post(self.url, {'aceitou_uso_dados': 'sim'})
        resposta = self.client.post(self.url, {})
        self.assertContains(resposta, 'Consentimento retirado.')
        consentimento = Consentimento.objects.get(usuario=self.usuario)
        self.assertFalse(consentimento.aceitou_uso_dados)
        self.assertIsNone(consentimento.data_consentimento)
