import re

from django.contrib.auth.hashers import check_password, make_password
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from banco_de_dados.models import Usuario


class TestesEsqueciSenha(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nome='Pessoa', email='senha@teste.com', senha=make_password('antiga123')
        )

    def pedir_link(self):
        self.client.post(reverse('EsqueciSenha'), {'email': 'senha@teste.com'})
        return re.search(r'http://testserver(/RedefinirSenha/\S+/)', mail.outbox[-1].body).group(1)

    def test_envia_email_com_link_para_email_cadastrado(self):
        resposta = self.client.post(reverse('EsqueciSenha'), {'email': 'Senha@Teste.com'})
        self.assertContains(resposta, 'Se esse e-mail estiver cadastrado')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['senha@teste.com'])
        self.assertIn('/RedefinirSenha/', mail.outbox[0].body)

    def test_email_nao_cadastrado_mostra_a_mesma_mensagem_sem_enviar(self):
        resposta = self.client.post(reverse('EsqueciSenha'), {'email': 'ninguem@teste.com'})
        self.assertContains(resposta, 'Se esse e-mail estiver cadastrado')
        self.assertEqual(len(mail.outbox), 0)

    def test_link_permite_trocar_a_senha(self):
        link = self.pedir_link()
        resposta = self.client.post(link, {'senha': 'nova1234', 'confirmar_senha': 'nova1234'})
        self.assertContains(resposta, 'Sua senha foi alterada com sucesso.')
        self.usuario.refresh_from_db()
        self.assertTrue(check_password('nova1234', self.usuario.senha))

    def test_entrar_com_a_nova_senha(self):
        link = self.pedir_link()
        self.client.post(link, {'senha': 'nova1234', 'confirmar_senha': 'nova1234'})
        resposta = self.client.post(reverse('Tela'), {'email': 'senha@teste.com', 'senha': 'nova1234'})
        self.assertRedirects(resposta, reverse('InicioLogado'))

    def test_link_nao_pode_ser_usado_duas_vezes(self):
        link = self.pedir_link()
        self.client.post(link, {'senha': 'nova1234', 'confirmar_senha': 'nova1234'})
        resposta = self.client.get(link)
        self.assertContains(resposta, 'Este link é inválido ou já expirou.')

    def test_link_alterado_e_invalido(self):
        resposta = self.client.get(reverse('RedefinirSenha', args=['token-falso']))
        self.assertContains(resposta, 'Este link é inválido ou já expirou.')

    def test_rejeita_senhas_diferentes_ou_curtas(self):
        link = self.pedir_link()
        resposta = self.client.post(link, {'senha': 'nova1234', 'confirmar_senha': 'outra123'})
        self.assertContains(resposta, 'As senhas não coincidem.')
        resposta = self.client.post(link, {'senha': '123', 'confirmar_senha': '123'})
        self.assertContains(resposta, 'pelo menos 6 caracteres')
        self.usuario.refresh_from_db()
        self.assertTrue(check_password('antiga123', self.usuario.senha))

    @override_settings(DEBUG=True)
    def test_em_desenvolvimento_o_link_aparece_na_tela(self):
        resposta = self.client.post(reverse('EsqueciSenha'), {'email': 'senha@teste.com'})
        self.assertContains(resposta, 'Modo de desenvolvimento')
        self.assertContains(resposta, '/RedefinirSenha/')

    @override_settings(DEBUG=True)
    def test_em_desenvolvimento_email_nao_cadastrado_nao_mostra_link(self):
        resposta = self.client.post(reverse('EsqueciSenha'), {'email': 'ninguem@teste.com'})
        self.assertNotContains(resposta, '/RedefinirSenha/')

    def test_em_producao_o_link_nao_aparece_na_tela(self):
        resposta = self.client.post(reverse('EsqueciSenha'), {'email': 'senha@teste.com'})
        self.assertNotContains(resposta, '/RedefinirSenha/')
