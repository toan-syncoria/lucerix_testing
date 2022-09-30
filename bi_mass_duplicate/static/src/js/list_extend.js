odoo.define('bi_mass_duplicate.ListExtend', function (require) {
"use strict";

var core = require('web.core');
var BasicController = require('web.BasicController');
var DataExport = require('web.DataExport');
//var Sidebar = require('web.Sidebar');
var session = require('web.session');
var _t = core._t;
var qweb = core.qweb;
var ListController = require('web.ListController');

var ListExtend = ListController.include({

	init: function (parent, model, renderer, params) {
		this._super.apply(this, arguments);
		this.hasSidebar = params.hasSidebar;
		this.toolbarActions = params.toolbarActions || {};
		this.editable = params.editable;
		this.noLeaf = params.noLeaf;
		this.selectedRecords = []; // there is no selected record by default
		this.isMassDuplicationEnable = true;
		this.isDomainSelected = false;
	},

	_getActionMenuItems: function (state) {
	    if (!this.hasActionMenus || !this.selectedRecords.length) {
            return null;
        }
        const props = this._super(...arguments);
        const otherActionItems = [];
        if (this.isExportEnable) {
            otherActionItems.push({
                description: _t("Export"),
                callback: () => this._onExportData()
            });
        }
        if (this.archiveEnabled) {
            otherActionItems.push({
                description: _t("Archive"),
                callback: () => {
                    Dialog.confirm(this, _t("Are you sure that you want to archive all the selected records?"), {
                        confirm_callback: () => this._toggleArchiveState(true),
                    });
                }
            }, {
                description: _t("Unarchive"),
                callback: () => this._toggleArchiveState(false)
            });
        }
        if (this.activeActions.delete) {
            otherActionItems.push({
                description: _t("Delete"),
                callback: () => this._onDeleteSelectedRecords()
            });
        }
        if (this.isMassDuplicationEnable) {
            otherActionItems.push({
                description: _t("Duplicate"),
                callback: () => this._onDuplicateRecord()
            });
        }
        return Object.assign(props, {
            items: Object.assign({}, this.toolbarActions, { other: otherActionItems }),
            context: state.getContext(),
            domain: state.getDomain(),
            isDomainSelected: this.isDomainSelected,
        });
	},

	_onDuplicateRecord: function () {
		var self = this;
		this.duplicateRecord(this.selectedRecords,self.modelName)
			.then(function () {
				
			});
	},

	duplicateRecord: function (recordIds,modelname) {
		var self = this;
		var i = null;
		var lst=[];
		// var m =self.model;
		var res = [];
		// var record = this.model.localData[recordIds];
		var records = _.map(recordIds, function (id) { return self.model.localData[id]; });
		var context =this.model._getContext(records);;
		for(var x =0;x<records.length;x++)
		{
			lst.push(records[x]);
		}
		return this._rpc({
				model : 'mass.duplicate',
				method : 'mass_copy',
				args :[1,lst],
				context: context,
				}).then(function () {
					self.update({});
                });
	},

});


return ListExtend;

});