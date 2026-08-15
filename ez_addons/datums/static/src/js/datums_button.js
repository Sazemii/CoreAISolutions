/** @odoo-module **/
import { registry } from "@web/core/registry";
import { xml, Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

export class DatumsButton extends Component {
    static template = xml`
        <div t-if="state.chatbotEnabled" class="o_chatbot_launcher_container">
            <button class="o_chatbot_launcher" t-on-click="onClickChatbot">
                <img
                    class="o_chatbot_logo me-2"
                    src="/datums/static/description/icon.png"
                    alt="Datums"
                />
                <span>Datums</span>
            </button>
            <div t-if="state.error" class="alert alert-danger mt-2 o_chatbot_error" role="alert">
                <t t-esc="state.error"/>
            </div>
        </div>
    `;

    state = useState({
        dbInfo: null,
        error: null,
        scriptsLoaded: false,
        chatbotEnabled: false,
    });

    setup() {
        this.orm = useService('orm');
        this.action = useService('action');

        onWillStart(async () => {
            this.state.chatbotEnabled = true;

            if (this.state.chatbotEnabled) {
                // Fetch dynamic companies config based on logged in user
                this.userCompaniesConfig = null;
                this.orm.silent.call(
                    'datums.script',
                    'get_user_companies_config',
                    []
                ).then((config) => {
                    this.userCompaniesConfig = config;
                }).catch((err) => {
                    console.error("Failed to fetch user companies config:", err);
                });

                // Load scripts without blocking the component mount (Fix Owl timeout)
                this.loadChatbotScripts();
                // Add polling to check when chatbot is actually ready
                this.pollForChatbot();
            }
        });

        // onMounted(async () => {
        //     // Check for pending action in session (e.g. from page reload redirect)
        //     try {
        //         const pendingAction = await rpc('/api/chatbot/get_pending_action');
        //         if (pendingAction) {
        //             this.action.doAction(pendingAction);
        //         }
        //     } catch (err) {
        //         console.error("Failed to check pending chatbot action:", err);
        //     }

        //     // Intercept clicks on links pointing to chatbot open tokens
        //     this.clickListener = async (ev) => {
        //         const anchor = ev.target.closest('a');
        //         if (anchor && anchor.href && anchor.href.includes('/chatbot/open/')) {
        //             ev.preventDefault();
        //             // Extract token
        //             const urlParts = anchor.href.split('/chatbot/open/');
        //             if (urlParts.length > 1) {
        //                 const token = urlParts[1].split('?')[0];
        //                 try {
        //                     const result = await rpc('/chatbot/get_action_by_token', { token });
        //                     if (result && result.success && result.action) {
        //                         this.action.doAction(result.action);
        //                     } else {
        //                         console.error("Failed to execute chatbot action directly:", result ? result.error : "No response");
        //                     }
        //                 } catch (err) {
        //                     console.error("Error executing chatbot action directly:", err);
        //                 }
        //             }
        //         }
        //     };
        //     window.addEventListener('click', this.clickListener);
        // });

        onWillUnmount(() => {
            if (this.clickListener) {
                window.removeEventListener('click', this.clickListener);
            }
        });
    }


    pollForChatbot(retryCount = 0) {
        if (retryCount > 60) { // Stop after 1 minute
            return;
        }

        // Check for specific datums identifiers found in diagnostic
        const botFound = window.DatumsChatbot || window.datums ||
            window.datumsConfig || window.webpackChunkdatums_bot ||
            document.querySelector('.datums-launcher') ||
            document.querySelector('[id*="datums"]');

        if (botFound) {
            this.state.scriptsLoaded = true;
            this.state.error = null;
            this.applyChatbotConfig();
            return;
        }

        setTimeout(() => this.pollForChatbot(retryCount + 1), 1000);
    }

    applyChatbotConfig(retryCount = 0) {
        if (retryCount > 30) { // Stop after 15 seconds
            return;
        }

        // Ensure both datumsConfig and userCompaniesConfig are loaded
        if (window.datumsConfig && typeof window.datumsConfig.setConfig === 'function' && this.userCompaniesConfig) {
            try {
                window.datumsConfig.setConfig(this.userCompaniesConfig);
                console.log("Datums Chatbot configuration successfully applied:", this.userCompaniesConfig);
            } catch (e) {
                console.error("Error setting datumsConfig:", e);
            }
        } else {
            setTimeout(() => this.applyChatbotConfig(retryCount + 1), 500);
        }
    }




    async loadChatbotScripts() {
        if (this.state.scriptsLoaded) {
            return;
        }

        try {
            // Fetch chatbot embed script from external API via Odoo proxy
            const payload = {};
            if (this.userCompaniesConfig) {
                payload.filters = this.userCompaniesConfig;
            }
            const res = await fetch('/datums/get_chatbot_script', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
            const data = await res.json();

            if (!data.success || !data.script_content) {
                console.warn("Chatbot script API error:", data.error || "No script content returned");
                this.state.scriptsLoaded = true;
                return;
            }

            // Load embed code from API
            if (data.script_content) {
                let embedCode = data.script_content;

                // Fix common encoding issues
                embedCode = embedCode
                    .replace(/\\x3C/g, '<')  // Fix \x3C to <
                    .replace(/\\x3E/g, '>')  // Fix \x3E to >
                    .replace(/\\x26/g, '&'); // Fix \x26 to &


                // Create a temporary div to parse the HTML
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = embedCode;

                // Extract and load all script tags
                const scriptTags = Array.from(tempDiv.getElementsByTagName('script'));

                for (const scriptTag of scriptTags) {
                    if (scriptTag.src) {
                        await this.loadScript(scriptTag.src, scriptTag.getAttribute('charset') || 'utf-8');
                        if (typeof window.datumsConfig !== 'undefined' && !window.datumsConfig.setCompanies) {
                            window.datumsConfig.setCompanies = function (companies) {
                                this.companies = companies;
                            };
                        }
                    } else if (scriptTag.textContent) {
                        this.loadInlineScript(scriptTag.textContent);
                    }
                }
            }

            this.state.scriptsLoaded = true;
            this.state.error = null; // Clear error on success
        } catch (error) {
            this.state.error = `Load Error: ${error.message}`;
        }
    }

    loadScript(src, charset = 'utf-8') {
        return new Promise((resolve) => {
            // Prevent duplicate loading
            if (document.querySelector(`script[src="${src}"]`)) {
                return resolve();
            }

            const script = document.createElement('script');
            script.src = src;
            script.async = false; // Maintain order
            script.defer = true; // Use defer to not block but maintain order
            if (charset) script.charset = charset;

            script.onload = () => {
                resolve();
            };

            script.onerror = (error) => {
                resolve(); // Continue to avoid blocking
            };

            document.head.appendChild(script);
        });
    }


    loadInlineScript(scriptContent) {
        const script = document.createElement('script');
        script.textContent = scriptContent;
        script.setAttribute('data-chatbot-inline', 'true');
        document.head.appendChild(script);
    }


    async onClickChatbot() {
        const results = {
            windowObjects: [],
            selectorsTried: [],
            cornerFound: false,
            eventsDispatched: false
        };

        // 1. Try global objects
        const triggers = [
            { name: 'DatumsChatbot', obj: window.DatumsChatbot, method: 'open' },
            { name: 'DatumsChatbot.show', obj: window.DatumsChatbot, method: 'show' },
            { name: 'datums.open', obj: window.datums, method: 'open' },
            { name: 'PrivyBot', obj: window.PrivyBot, method: 'show' },
            { name: 'PrivyChat', obj: window.PrivyChat, method: 'open' },
            { name: 'chatbot', obj: window.chatbot, method: 'open' }
        ];

        for (const t of triggers) {
            if (t.obj && typeof t.obj[t.method] === 'function') {
                try {
                    t.obj[t.method]();
                    return;
                } catch (e) {
                    results.windowObjects.push(`${t.name}: error`);
                }
            } else {
                results.windowObjects.push(`${t.name}: not found`);
            }
        }

        // 2. Deep selector search (including IFrames)
        const targetSelectors = [
            '#datums-launcher', '.datums-launcher', '.datums-chatbot-launcher',
            '.datums-widget-launcher', '.datums-bubble', '.datums-icon',
            'iframe[src*="datums"]', '[class*="datums"]', '[id*="datums"]',
            '.privy-launcher', '.privy-toggle', '.chatbot-launcher'
        ];

        const searchInContext = (root) => {
            for (const selector of targetSelectors) {
                const elements = root.querySelectorAll(selector);
                for (const el of elements) {
                    if (el.classList.contains('o_chatbot_launcher')) continue;

                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        el.click();
                        // Also try a simulated click for complex widgets
                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                        return true;
                    }
                }
            }
            // Check if any element is an iframe and search inside it
            const iframes = root.querySelectorAll('iframe');
            for (const iframe of iframes) {
                try {
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (searchInContext(doc)) return true;
                } catch (e) {
                    // Ignore cross-origin errors
                }
            }
            return false;
        };

        if (searchInContext(document)) {
            return;
        }

        // 3. Fallback: Corner search (Look in the bottom-right corner)
        const allInteractive = document.querySelectorAll('button, div[role="button"], img, svg, iframe');
        for (const el of allInteractive) {
            if (el.classList.contains('o_chatbot_launcher')) continue;

            const rect = el.getBoundingClientRect();
            // Check bottom-right 250px
            if (rect.right > window.innerWidth - 250 && rect.bottom > window.innerHeight - 250) {
                if (rect.width > 10) {
                    const identity = (el.className + el.id).toLowerCase();
                    if (identity.includes('chat') || identity.includes('bot') || identity.includes('datum')) {
                        el.click();
                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                        results.cornerFound = true;
                    }
                }
            }
        }

        if (results.cornerFound) {
            return;
        }

        // 4. Dispatch fallback events
        window.dispatchEvent(new CustomEvent('chatbot:open'));
        window.dispatchEvent(new CustomEvent('chatbot:show'));
    }


}

const mainComponents = registry.category("main_components");
if (!mainComponents.contains("DatumsButton")) {
    mainComponents.add("DatumsButton", {
        Component: DatumsButton,
    });
}
