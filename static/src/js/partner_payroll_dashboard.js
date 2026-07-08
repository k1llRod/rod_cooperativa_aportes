odoo.define('rod_cooperativa_aportes.PartnerPayrollDashboard', function (require) {
"use strict";

var core = require('web.core');
var ListController = require('web.ListController');
var ListModel = require('web.ListModel');
var ListRenderer = require('web.ListRenderer');
var ListView = require('web.ListView');
var view_registry = require('web.view_registry');

var QWeb = core.qweb;

// 1. RENDERIZADOR: Controla el diseño en pantalla y el evento "Click"
var PartnerPayrollDashboardRenderer = ListRenderer.extend({
    events: _.extend({}, ListRenderer.prototype.events, {
        'click .o_dashboard_action': '_onDashboardActionClicked',
    }),

    _renderView: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            // Recuperamos los valores procesados por el Model
            var values = self.state.dashboardValues || {};
            var dashboard_html = QWeb.render('rod_cooperativa_aportes.PartnerPayrollDashboard', {
                values: values,
            });
            // Quitamos duplicados previos si existen e inyectamos arriba de la tabla
            self.$el.parent().find(".o_partner_payroll_dashboard").remove();
            self.$el.prepend(dashboard_html);
        });
    },

    // Al hacer clic, dispara la acción con el contexto asignado en el botón XML
    _onDashboardActionClicked: function (e) {
        e.preventDefault();
        var $action = $(e.currentTarget);
        this.trigger_up('dashboard_open_action', {
            action_name: "rod_cooperativa_aportes.action_partner_payroll", // Tu acción nativa
            action_context: $action.attr('context'),
        });
    },
});

// 2. MODELO: Se encarga de llamar al backend de forma asíncrona (RPC)
var PartnerPayrollDashboardModel = ListModel.extend({
    init: function () {
        this.dashboardValues = {};
        this._super.apply(this, arguments);
    },

    __get: function (localID) {
        var result = this._super.apply(this, arguments);
        if (_.isObject(result)) {
            result.dashboardValues = this.dashboardValues[localID];
        }
        return result;
    },

    __load: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },

    __reload: function () {
        return this._loadDashboard(this._super.apply(this, arguments));
    },

    _loadDashboard: function (super_def) {
        var self = this;
        var dashboard_def = this._rpc({
            model: 'partner.payroll',
            method: 'retrieve_dashboard_data',
        });
        return Promise.all([super_def, dashboard_def]).then(function (results) {
            var id = results[0];
            self.dashboardValues[id] = results[1];
            return id;
        });
    },
});

// 3. CONTROLADOR: Ejecuta la recarga de la vista aplicando el nuevo filtro
var PartnerPayrollDashboardController = ListController.extend({
    custom_events: _.extend({}, ListController.prototype.custom_events, {
        dashboard_open_action: '_onDashboardOpenAction',
    }),

    _onDashboardOpenAction: function (e) {
        return this.do_action(e.data.action_name, {
            additional_context: JSON.parse(e.data.action_context)
        });
    },
});

// 4. VISTA: Ensambla los tres componentes anteriores
var PartnerPayrollDashboardListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Model: PartnerPayrollDashboardModel,
        Renderer: PartnerPayrollDashboardRenderer,
        Controller: PartnerPayrollDashboardController,
    }),
});

// Registramos el alias para usar en el XML (js_class)
view_registry.add('partner_payroll_dashboard_list', PartnerPayrollDashboardListView);

});