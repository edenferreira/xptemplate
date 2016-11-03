XPTemplate priority=personal

XPT angconf " Config
(function () {
    'use strict';

    var inject = [];
    function config() {
        `//code here^
    }
    config.$inject = inject;

    angular.module('`module_name^').config(config);
}());

XPT angfac " Factory
(function () {
    'use strict';

    var inject = [];
    function `factory_name^Factory() {
        return function `factory_name^() {
            `//code here^
        };
    }
    `factory_name^Factory.$inject = inject;

    angular.module('`module_name^').factory('`factory_name^', `factory_name^Factory);
}());

XPT angser " Service
(function () {
    'use strict';

    var inject = [];
    function `service_name^Service() {
        `//code here^
        return {
        };
    }
    `service_name^Service.$inject = inject;

    angular.module('`module_name^').factory('`service_name^', `service_name^Service);
}());

XPT angcom " Component
(function () {
    'use strict';

    var inject = [];
    function `component_name^Controller() {
        var ctrl = this;
    }
    `component_name^Controller.$inject = inject;

    angular.module('`module_name^').component('`component_name^', {
        bindings: {
        },
        controller: `component_name^Controller,
        templateUrl: '`template_url^'
    });
}());

XPT angrun " Run
(function () {
    'use strict';

    var inject = [];
    function run() {
        `//code here^
    }
    run.$inject = inject;

    angular.module('`module_name^').run(run);
}())

XPT ctmet " Controller method
ctrl.`method_name^ = `method_name^;
