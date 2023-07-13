# -*- coding: utf-8 -*-
# from odoo import http


# class RodCooperativaAportes(http.Controller):
#     @http.route('/rod_cooperativa_aportes/rod_cooperativa_aportes', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rod_cooperativa_aportes/rod_cooperativa_aportes/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rod_cooperativa_aportes.listing', {
#             'root': '/rod_cooperativa_aportes/rod_cooperativa_aportes',
#             'objects': http.request.env['rod_cooperativa_aportes.rod_cooperativa_aportes'].search([]),
#         })

#     @http.route('/rod_cooperativa_aportes/rod_cooperativa_aportes/objects/<model("rod_cooperativa_aportes.rod_cooperativa_aportes"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rod_cooperativa_aportes.object', {
#             'object': obj
#         })
