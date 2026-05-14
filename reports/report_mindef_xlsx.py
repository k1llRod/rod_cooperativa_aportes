from odoo import models


class MindefReportXlsx(models.AbstractModel):
    _name = 'report.rod_cooperativa_aportes.report_mindef_xlsx_abstract'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Planilla Homologación')

        # --- ESTILOS ---
        title_style = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'bg_color': '#4F81BD', 'font_color': 'white'
        })
        header_style = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#D9E1F2', 'align': 'center'
        })
        sub_title_style = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
        data_style = workbook.add_format({'border': 1})
        money_style = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        center_style = workbook.add_format({'border': 1, 'align': 'center'})

        # Estilo para la línea separadora final de sección
        separator_style = workbook.add_format({'top': 5, 'top_color': '#4F81BD'})

        # --- ENCABEZADO ---
        sheet.merge_range('A1:G1', 'PLANILLA DE HOMOLOGACIÓN Y RESUMEN MINDEF', title_style)
        sheet.write('A2', 'Periodo:', sub_title_style)
        sheet.write('B2', data.get('period'), data_style)
        sheet.write('A3', 'Fecha Reporte:', sub_title_style)
        sheet.write('B3', data.get('date'), data_style)

        row = 5

        # --- SECCIÓN 1: REGISTROS DEL ARCHIVADOR (CONCILIACIÓN) ---
        sections = [
            ('BORRADOR (Draft)', data.get('ids_draft'), '#D9E1F2'),
            ('NO CONCILIADOS', data.get('ids_no_reconciled'), '#FCE4D6'),
            ('CONCILIADOS', data.get('ids_reconciled'), '#E2EFDA'),
            ('OBSERVADOS', data.get('ids_observed'), '#FFF2CC'),
        ]

        for title, ids, color in sections:
            if not ids:
                continue

            section_style = workbook.add_format({'bold': True, 'bg_color': color, 'border': 1})
            sheet.merge_range(row, 0, row, 6, f"ESTADO ARCHIVADOR: {title} - Total: {len(ids)}", section_style)
            row += 1

            headers = ['N°', 'Grado', 'Mención', 'Nombre Completo', 'Monto (Bs)', 'Gestión', 'Mes']
            for col, text in enumerate(headers):
                sheet.write(row, col, text, header_style)
            row += 1

            counter = 1
            # Modelo: nominal.relationship.mindef.contributions
            records = self.env['nominal.relationship.mindef.contributions'].browse(ids)
            # Ordenar alfabéticamente para mejor lectura
            records = sorted(records, key=lambda x: x.name_complete or '')

            for rec in records:
                sheet.write(row, 0, counter, center_style)
                sheet.write(row, 1, rec.degree or '', data_style)
                sheet.write(row, 2, rec.mension or '', data_style)
                sheet.write(row, 3, rec.name_complete or '', data_style)
                sheet.write(row, 4, rec.amount_bs or 0.0, money_style)
                sheet.write(row, 5, rec.management or '', data_style)
                sheet.write(row, 6, rec.month or '', data_style)
                row += 1
                counter += 1

            row += 2  # Espacio entre secciones

        # --- SECCIÓN 2: ASOCIADOS ACTIVOS SIN APORTE (CRUCE PAYROLL PAYMENTS) ---
        ids_no_contrib = data.get('ids_no_contribution_active')
        if ids_no_contrib:
            # Color distintivo para alertas de falta de aporte
            no_contrib_style = workbook.add_format({'bold': True, 'bg_color': '#FFC7CE', 'border': 1})
            sheet.merge_range(row, 0, row, 6, f"SOCIOS SERVICIO ACTIVO SIN APORTE - Total: {len(ids_no_contrib)}",
                              no_contrib_style)
            row += 1

            headers_p = ['N°', 'Cód. Socio', 'CI / Ciudad', 'Nombre Completo', 'Situación', 'Periodo', 'Estado Pago']
            for col, text in enumerate(headers_p):
                sheet.write(row, col, text, header_style)
            row += 1

            counter_p = 1
            # Modelo: payroll.payments
            records_p = self.env['payroll.payments'].browse(ids_no_contrib)
            records_p = sorted(records_p, key=lambda x: x.partner_name or '')

            for rec_p in records_p:
                sheet.write(row, 0, counter_p, center_style)
                sheet.write(row, 1, rec_p.partner_code_contact or '', data_style)
                # Datos desde el partner relacionado
                ci_city = f"{rec_p.partner_payroll_id.partner_id.vat or ''} / {rec_p.city or ''}"
                sheet.write(row, 2, ci_city, data_style)
                sheet.write(row, 3, rec_p.partner_name or '', data_style)
                sheet.write(row, 4, 'SERVICIO ACTIVO', data_style)
                sheet.write(row, 5, rec_p.period_register or '', data_style)
                sheet.write(row, 6, 'SIN APORTE (no_contribution)', data_style)
                row += 1
                counter_p += 1

            # Línea de cierre estética
            for col in range(7):
                sheet.write(row, col, '', separator_style)

        # --- CONFIGURACIÓN DE COLUMNAS ---
        sheet.set_column('A:A', 5)  # N°
        sheet.set_column('B:B', 12)  # Grado / Cód Socio
        sheet.set_column('C:C', 18)  # Mención / CI
        sheet.set_column('D:D', 40)  # Nombre Completo
        sheet.set_column('E:E', 15)  # Monto / Situación
        sheet.set_column('F:F', 10)  # Gestión / Periodo
        sheet.set_column('G:G', 15)  # Mes / Estado Pago