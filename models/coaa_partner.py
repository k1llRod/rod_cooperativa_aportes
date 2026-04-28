from odoo import api, fields, models, tools, _

class CoaaPartner(models.Model):
    _name = 'coaa_partner'
    cod = fields.Char(string='cod')
    codfza = fields.Char(string='codfza')
    apat = fields.Char(string='apat')
    amat = fields.Char(string='amat')
    nom = fields.Char(string='nom')
    eciv = fields.Char(string='eciv')
    sexo = fields.Char(string='sexo')
    fecnac = fields.Date(string='fecnac')
    escalf = fields.Char(string='escalf')
    codgra = fields.Char(string='codgra')
    codarm = fields.Char(string='codarm')
    codrep = fields.Char(string='codrep')
    coddip = fields.Char(string='coddip')
    ci = fields.Char(string='ci')
    lp = fields.Char(string='lp')
    dom = fields.Char(string='dom')
    fdom = fields.Char(string='fdom')
    tpers = fields.Char(string='tpers')
    ref1 = fields.Char(string='ref1')
    falta = fields.Char(string='falta')
    fbaja = fields.Date(string='fbaja')
    usralt = fields.Char(string='usralt')
    fusr = fields.Char(string='fusr')
    usrupd = fields.Char(string='usrupd')
    fupd = fields.Char(string='fupd')





