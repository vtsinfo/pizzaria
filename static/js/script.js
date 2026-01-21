document.addEventListener('DOMContentLoaded', function () {
    initAIWidget();
    initInactivityFeatures();
    initSoundSettings();
    playWelcomeMessage();
});

function initAIWidget() {
    const widget = document.getElementById('ai-widget-container');
    if (!widget) return;

    const toggleBtn = document.getElementById('ai-toggle-btn');
    const closeBtn = document.getElementById('close-ai-btn');
    const clearBtn = document.getElementById('clear-ai-btn');
    const badge = document.querySelector('.ai-notification-badge');
    const input = document.getElementById('ai-input');
    const sendBtn = document.getElementById('ai-send-btn');
    const messagesContainer = document.getElementById('ai-messages');

    let knowledgeBase = {};
    let fallbackResponse = "Desculpe, não entendi.";
    let awaitingNeighborhood = false;
    let awaitingMenuCategory = false;
    let checkoutState = null; // null, 'method', 'cep', 'address_number', 'switch_method', 'check_saved', 'name', 'phone', 'coupon', 'payment', 'payment_change', 'obs'
    let orderData = {};
    let cart = [];
    let currentUnit = null;
    let currentWaitTime = "40-50 min";

    // Unidades da Pizzaria (Carregadas via API)
    let units = [];

    // Carrega Configurações Gerais e Unidades
    fetch('/api/config/geral')
        .then(r => r.json())
        .then(data => {
            if (data.tempo_espera) currentWaitTime = data.tempo_espera;
            if (data.units && Array.isArray(data.units)) units = data.units;
            // Store global config for voice access
            window.siteConfig = data;
            // Fallback se não houver unidades configuradas
            if (units.length === 0) {
                units = [{ name: "Unidade Principal", lat: -23.5505, lon: -46.6333, address: "Endereço não configurado", phone: "5511999999999" }];
            }
        })
        .catch(e => console.log("Erro ao carregar config:", e));

    // Função para calcular distância (Haversine Formula)
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Raio da Terra em km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    // Função para calcular taxa de entrega estimada
    function calculateDeliveryFee(distance) {
        // Taxa base R$ 3,00 + R$ 1,50 por km
        const fee = 3.00 + (distance * 1.50);
        return fee.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }

    // Função para verificar status da loja
    function getStoreStatus() {
        const now = new Date();
        const day = now.getDay(); // 0=Dom, 1=Seg, ...
        const hour = now.getHours();
        const minutes = now.getMinutes();
        const currentTime = hour + (minutes / 60);

        // Horários: 18:00 às 23:30 (Dom-Qui) / 18:00 às 00:00 (Sex-Sáb)
        const openTime = 18.0;
        let closeTime = 23.5; // 23:30
        let closeTimeStr = "23:30";

        if (day === 5 || day === 6) {
            closeTime = 24.0;
            closeTimeStr = "00:00";
        }

        const isOpen = currentTime >= openTime && currentTime < closeTime;
        let message = "";

        if (isOpen) {
            message = `Estamos abertos até às ${closeTimeStr}!`;
        } else {
            if (currentTime < openTime) {
                message = `Estamos fechados agora. Abrimos às 18:00.`;
            } else {
                message = `Estamos fechados. Voltamos amanhã às 18:00.`;
            }
        }

        return { isOpen, message };
    }

    // Processar verificação de CEP
    async function processDeliveryCheck(cep) {
        awaitingNeighborhood = false;
        try {
            // Busca coordenadas do CEP (Nominatim OpenStreetMap - Gratuito)
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&countrycodes=br&limit=1&postalcode=${cep}&addressdetails=1`);
            const data = await response.json();

            if (!data || data.length === 0) {
                awaitingNeighborhood = true;
                return "Não consegui localizar esse CEP. 😓 Poderia me dizer qual é o seu **bairro**?";
            }

            const userLat = parseFloat(data[0].lat);
            const userLon = parseFloat(data[0].lon);

            let nearestUnit = null;
            let minDistance = Infinity;

            units.forEach(unit => {
                const dist = calculateDistance(userLat, userLon, unit.lat, unit.lon);
                if (dist < minDistance) {
                    minDistance = dist;
                    nearestUnit = unit;
                }
            });

            const distFormatted = minDistance.toFixed(1);
            const deliveryFee = calculateDeliveryFee(minDistance);
            const storeStatus = getStoreStatus();

            const address = data[0].address || {};
            const street = address.road || address.street || address.pedestrian || address.footway || "Rua identificada pelo CEP";

            if (minDistance <= 6) {
                currentUnit = nearestUnit;

                let msg = `Boas notícias! 🎉 Localizei a rua <strong>${street}</strong>.<br>Você está a <strong>${distFormatted}km</strong> da unidade <strong>${nearestUnit.name}</strong>.<br>Fazemos entrega aí sim!`;
                msg += `<br>💰 <strong>Taxa de entrega estimada:</strong> ${deliveryFee}`;

                if (!storeStatus.isOpen) {
                    msg += `<br><br>⚠️ <strong>${storeStatus.message}</strong> 🕒<br>Mas você pode deixar agendado!`;
                }

                msg += ` <a href="https://wa.me/${nearestUnit.phone}?text=Olá, gostaria de fazer um pedido para o CEP ${cep}" target="_blank" class="text-white text-decoration-underline">Clique aqui para pedir no WhatsApp</a>.`;
                return msg;
            } else {
                return `Poxa! 😕 A rua <strong>${street}</strong> fica a <strong>${distFormatted}km</strong> da unidade mais próxima (${nearestUnit.name}). Para garantir a qualidade, nosso delivery vai até 6km.<br><br>Mas não fique na vontade! 🍕<br>Venha nos visitar em <strong>${nearestUnit.address}</strong>. O rodízio está incrível e o ambiente é perfeito para sua família. Vale a pena o passeio!`;
            }

        } catch (error) {
            console.error("Erro ao buscar CEP", error);
            return "Tive um problema técnico ao verificar seu CEP. Pode tentar novamente ou chamar no WhatsApp?";
        }
    }

    // Processar verificação de Bairro
    async function processNeighborhoodCheck(neighborhood) {
        try {
            // Busca coordenadas do Bairro (Adiciona "SP" para contexto)
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&countrycodes=br&limit=1&q=${encodeURIComponent(neighborhood + ", SP")}`);
            const data = await response.json();

            if (!data || data.length === 0) {
                return "Também não consegui localizar o bairro. 😕<br><br>Mas não fique na vontade! 🍕<br>Venha nos visitar em uma de nossas unidades. O rodízio está incrível e vale a pena o passeio!<br><br><a href='https://www.google.com/maps/search/Pizzaria+Colonial+São+Paulo' target='_blank' class='text-white text-decoration-underline'>Encontrar a unidade mais próxima no Mapa</a>";
            }

            const userLat = parseFloat(data[0].lat);
            const userLon = parseFloat(data[0].lon);

            let nearestUnit = null;
            let minDistance = Infinity;

            units.forEach(unit => {
                const dist = calculateDistance(userLat, userLon, unit.lat, unit.lon);
                if (dist < minDistance) {
                    minDistance = dist;
                    nearestUnit = unit;
                }
            });

            const distFormatted = minDistance.toFixed(1);
            const deliveryFee = calculateDeliveryFee(minDistance);
            const storeStatus = getStoreStatus();

            if (minDistance <= 6) {
                currentUnit = nearestUnit;
                let msg = `Encontrei seu bairro! 🎉 Você está a aprox. <strong>${distFormatted}km</strong> da unidade <strong>${nearestUnit.name}</strong>.<br>Fazemos entrega aí sim!`;
                msg += `<br>💰 <strong>Taxa de entrega estimada:</strong> ${deliveryFee}`;

                if (!storeStatus.isOpen) {
                    msg += `<br><br>⚠️ <strong>${storeStatus.message}</strong> 🕒<br>Mas você pode deixar agendado!`;
                }

                msg += ` <a href="https://wa.me/${nearestUnit.phone}?text=Olá, gostaria de fazer um pedido para o bairro ${neighborhood}" target="_blank" class="text-white text-decoration-underline">Clique aqui para pedir no WhatsApp</a>.`;
                return msg;
            } else {
                return `Poxa! 😕 O bairro ${neighborhood} fica a aprox. <strong>${distFormatted}km</strong> da unidade mais próxima (${nearestUnit.name}). Para garantir a qualidade, nosso delivery vai até 6km.<br><br>Mas não fique na vontade! 🍕<br>Venha nos visitar em <strong>${nearestUnit.address}</strong>.`;
            }
        } catch (error) {
            console.error("Erro ao buscar Bairro", error);
            return "Tive um problema técnico ao verificar seu bairro. Pode tentar chamar no WhatsApp?";
        }
    }

    // --- Favoritos ---
    function getFavorites() {
        return JSON.parse(localStorage.getItem('vts_pizza_favorites')) || [];
    }

    function isFavorite(name) {
        return getFavorites().some(f => f.name === name);
    }

    function toggleFavorite(name, price, desc) {
        let favs = getFavorites();
        const index = favs.findIndex(f => f.name === name);
        if (index > -1) {
            favs.splice(index, 1);
        } else {
            favs.push({ name, price, desc });
        }
        localStorage.setItem('vts_pizza_favorites', JSON.stringify(favs));
    }

    function showFavorites() {
        const favs = getFavorites();
        if (favs.length === 0) {
            addMessage("Você ainda não tem favoritos! ⭐<br>Clique na estrela ao lado dos itens do cardápio para salvar.", 'bot');
            return;
        }

        let html = "<strong>⭐ Seus Favoritos:</strong><br>";
        favs.forEach(item => {
            html += `<div style="margin-bottom: 8px; padding: 4px 0; display: flex; align-items: center; justify-content: space-between;">
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between;"><strong>${item.name}</strong> <span style="margin-left: 5px;">${item.price}</span></div>
                            <div style="font-size: 0.85em; opacity: 0.8; line-height: 1.2;">${item.desc || ''}</div>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center; margin-left: 5px;">
                            <button class="fav-btn" data-name="${item.name}" data-price="${item.price}" data-desc="${item.desc || ''}" style="background: transparent; border: none; cursor: pointer; font-size: 1.4em; color: #ffc107; padding: 0;">⭐</button>
                            <button class="add-cart-btn" data-name="${item.name}" data-price="${item.price}" style="background: #28a745; border: none; color: white; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-weight: bold; flex-shrink: 0;">+</button>
                        </div>
                     </div>`;
        });

        html += `<div style="margin-top: 15px; text-align: center;">
                    <button class="back-to-menu-btn" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 0.9em; transition: background 0.2s;">⬅ Voltar ao Menu</button>
                 </div>`;
        addMessage(html, 'bot');
    }

    // --- Avaliação ---
    function showRatingUI() {
        let html = `<div class="rating-container" style="text-align: center; margin-top: 15px; padding-top: 10px; border-top: 1px dashed rgba(255,255,255,0.2);">
                        <p style="margin-bottom: 5px;">Como foi sua experiência?</p>
                        <div style="font-size: 1.8em; cursor: pointer; letter-spacing: 5px;">
                            <span class="rate-star" data-val="1">☆</span><span class="rate-star" data-val="2">☆</span><span class="rate-star" data-val="3">☆</span><span class="rate-star" data-val="4">☆</span><span class="rate-star" data-val="5">☆</span>
                        </div>
                    </div>`;
        addMessage(html, 'bot');
    }

    // Remover do Carrinho
    function removeFromCart(index) {
        if (index >= 0 && index < cart.length) {
            cart.splice(index, 1);
            showCart();
        }
    }

    // Exibir Carrinho (Editável)
    function showCart() {
        if (cart.length === 0) {
            addMessage("Seu carrinho ficou vazio! 🛒 Que tal adicionar algo?", 'bot');
            showMenuCategories();
            return;
        }

        let total = 0;
        let html = `🛒 <strong>Seu Carrinho:</strong><br>`;

        cart.forEach((item, index) => {
            html += `<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 2px;">
                        <span>${item.name} <small>(${item.price})</small></span>
                        <button class="remove-cart-item-btn" data-index="${index}" style="background: #dc3545; border: none; color: white; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-weight: bold; margin-left: 10px; display: flex; align-items: center; justify-content: center;" title="Remover">×</button>
                     </div>`;
            const priceVal = parseFloat(item.price.replace(/[^\d,]/g, '').replace(',', '.'));
            if (!isNaN(priceVal)) total += priceVal;
        });

        const totalFormatted = total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        html += `<div style="margin-top: 10px; font-weight: bold;">Total: ${totalFormatted}</div>`;

        html += `<div style="margin-top: 15px; display: flex; gap: 10px; justify-content: center;">
                    <button class="back-to-menu-btn" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 8px 12px; border-radius: 15px; cursor: pointer; font-size: 0.9em;">+ Itens</button>
                    <button class="finalize-order-btn" style="background: #28a745; border: none; color: white; padding: 8px 12px; border-radius: 15px; cursor: pointer; font-size: 0.9em;">✅ Concluir</button>
                 </div>`;

        addMessage(html, 'bot');
    }

    // Adicionar ao Carrinho
    function addToCart(name, price) {
        cart.push({ name, price });
        addMessage(`✅ <strong>${name}</strong> adicionado!<br>🛒 Carrinho: ${cart.length} item(ns).<br><button class="view-cart-btn" style="margin-top: 8px; background: #17a2b8; border: none; color: white; padding: 6px 12px; border-radius: 15px; cursor: pointer; font-size: 0.9em;">Ver Carrinho / Finalizar</button>`, 'bot');

        // Sugestão Inteligente de Bebidas
        const isDrink = (n) => /coca|guaraná|suco|cerveja|refri|água|fanta|sprite|soda|bebida|h2oh|schweppes/i.test(n);
        const hasDrink = cart.some(item => isDrink(item.name));

        if (!isDrink(name) && !hasDrink) {
            setTimeout(() => {
                addMessage(`Que tal uma bebida geladinha para acompanhar? 🥤<br><button class="show-drinks-btn" style="background: #6c757d; border: none; color: white; padding: 6px 12px; border-radius: 15px; cursor: pointer; font-size: 0.85em; margin-top: 5px;">Ver Bebidas</button>`, 'bot');
            }, 1200);
        }
    }

    // Finalizar Pedido
    function finalizeOrder() {
        if (cart.length === 0) {
            addMessage("Seu carrinho está vazio! 🛒 Adicione itens do cardápio primeiro.", 'bot');
            return;
        }

        checkoutState = 'method';
        orderData = { method: '', name: '', phone: '', cep: '', fee: 'R$ 0,00', obs: '', discount: null, paymentMethod: '', change: '' };

        addMessage(`Vamos fechar seu pedido! 📝<br>Como você prefere receber?<br>
            <button class="chat-option-btn" data-val="Entrega" style="background: #ffc107; border: none; color: #000; padding: 8px 16px; margin: 5px; border-radius: 20px; cursor: pointer; font-weight: bold;">🛵 Entrega</button>
            <button class="chat-option-btn" data-val="Retirada" style="background: #17a2b8; border: none; color: #fff; padding: 8px 16px; margin: 5px; border-radius: 20px; cursor: pointer; font-weight: bold;">🏪 Retirada</button>`, 'bot');
    }

    // Concluir Checkout e Gerar Link
    async function finishCheckout() {
        // Salvar dados no localStorage
        localStorage.setItem('vts_user_name', orderData.name);
        localStorage.setItem('vts_user_phone', orderData.phone);

        let total = 0;
        let msg = `Olá! Gostaria de fazer um pedido (${orderData.method}):\n\n`;
        msg += `👤 *Cliente:* ${orderData.name}\n`;
        msg += `📱 *Tel:* ${orderData.phone}\n`;
        msg += `💳 *Pagamento:* ${orderData.paymentMethod} ${orderData.change ? '(' + orderData.change + ')' : ''}\n`;

        if (orderData.method === 'Entrega') {
            const fullAddress = orderData.street ? `${orderData.street}, ${orderData.number_complement} (${orderData.cep})` : orderData.cep;
            msg += `📍 *Endereço:* ${fullAddress}\n`;
        }

        msg += `\n🛒 *Itens:* \n`;

        cart.forEach(item => {
            msg += `- ${item.name} (${item.price})\n`;
            const priceVal = parseFloat(item.price.replace(/[^\d,]/g, '').replace(',', '.'));
            if (!isNaN(priceVal)) total += priceVal;
        });

        // Adiciona taxa de entrega se houver
        const feeVal = parseFloat(orderData.fee.replace(/[^\d,]/g, '').replace(',', '.'));
        if (!isNaN(feeVal) && feeVal > 0) total += feeVal;

        // Aplica Desconto
        if (orderData.discount) {
            let discountVal = 0;
            if (orderData.discount.tipo === 'fixo') discountVal = parseFloat(orderData.discount.valor);
            else discountVal = total * (parseFloat(orderData.discount.valor) / 100);

            total -= discountVal;
            if (total < 0) total = 0;

            msg += `\n🎟️ *Cupom (${orderData.discount.codigo}):* -${discountVal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`;
        }

        const totalFormatted = total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        // Enviar para o Painel Admin (API)
        try {
            const response = await fetch('/api/pedido/novo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    customer: orderData.name,
                    phone: orderData.phone,
                    method: orderData.method,
                    address: orderData.method === 'Entrega' ? (orderData.street ? `${orderData.street}, ${orderData.number_complement} (${orderData.cep})` : orderData.cep) : 'Retirada na Loja',
                    items: cart,
                    total: totalFormatted,
                    obs: orderData.obs,
                    coupon: orderData.discount ? orderData.discount.codigo : null,
                    fee: orderData.fee,
                    paymentMethod: orderData.paymentMethod,
                    change: orderData.change
                })
            });
            const resData = await response.json();
            if (!resData.success) {
                addMessage(`❌ <strong>Erro no Pedido:</strong> ${resData.message}`, 'bot');
                return;
            }
        } catch (err) {
            console.error("Erro ao enviar pedido", err);
            addMessage("❌ Erro de conexão ao registrar pedido. Tente novamente.", 'bot');
            return;
        }

        if (orderData.method === 'Entrega') {
            msg += `\n🛵 *Taxa de Entrega:* ${orderData.fee}`;
        }

        msg += `\n💰 *Total Final:* ${totalFormatted}`;

        if (orderData.obs) {
            msg += `\n\n📝 *Obs:* ${orderData.obs}`;
        }

        const unit = currentUnit || units[0];
        const link = `https://wa.me/${unit.phone}?text=${encodeURIComponent(msg)}`;

        let html = `✅ <strong>Pedido Pronto!</strong><br>`;
        html += `Tipo: <strong>${orderData.method}</strong><br>`;
        html += `Cliente: ${orderData.name}<br>`;
        html += `Pagamento: <strong>${orderData.paymentMethod}</strong> ${orderData.change ? '(' + orderData.change + ')' : ''}<br>`;
        html += `Total: <strong>${totalFormatted}</strong><br>`;

        if (orderData.discount) {
            html += `<small style="color: #28a745;">(Desconto aplicado: ${orderData.discount.codigo})</small><br>`;
        }

        if (orderData.obs) html += `Obs: <small>${orderData.obs}</small><br>`;

        html += `<br><br>📍 Unidade: ${unit.name}`;
        html += `<br><br><a href="${link}" target="_blank" style="background-color: #25D366; color: white; padding: 10px 20px; border-radius: 20px; text-decoration: none; display: inline-block; font-weight: bold;">📲 Enviar para WhatsApp</a>`;

        addMessage(html, 'bot');

        setTimeout(() => showRatingUI(), 1500);

        cart = [];
        checkoutState = null;
        orderData = {};
    }

    // Função para exibir categorias do menu
    function showMenuCategories(introText = "Com certeza! O que você manda hoje? 😋") {
        awaitingMenuCategory = true;
        addMessage(`${introText}<br>Digite o número ou nome da opção:<br>1️⃣ <strong>Pizzas</strong><br>2️⃣ <strong>Churrasco</strong><br>3️⃣ <strong>Hambúrgueres</strong><br>4️⃣ <strong>Marmitex</strong><br>5️⃣ <strong>Bebidas</strong><br>6️⃣ <strong>Ver Tudo</strong><br>7️⃣ <strong>⭐ Favoritos</strong>`, 'bot');
    }

    // Sugerir Destaques (IA)
    async function suggestHighlights() {
        try {
            addMessage("Deixa comigo! Vou separar umas opções deliciosas para você... 👩‍🍳", 'bot');

            const response = await fetch('/api/cardapio');
            if (!response.ok) throw new Error('Erro na API');

            const menu = await response.json();
            let allItems = [];

            // Coleta todos os itens visíveis e não esgotados
            for (const cat in menu) {
                if (menu[cat]) {
                    menu[cat].forEach(item => {
                        if (item.visivel !== false && !item.esgotado) {
                            allItems.push(item);
                        }
                    });
                }
            }

            if (allItems.length === 0) {
                addMessage("No momento estamos atualizando nosso cardápio. Tente ver as categorias!", 'bot');
                showMenuCategories();
                return;
            }

            // Embaralha e pega 3
            allItems.sort(() => 0.5 - Math.random());
            const suggestions = allItems.slice(0, 3);

            let html = "<strong>🌟 Minhas sugestões de hoje:</strong><br>";

            suggestions.forEach(item => {
                html += `<div style="margin-top: 10px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 8px;">
                            <div style="font-weight: bold; color: #ffc107;">${item.nome}</div>
                            <div style="font-size: 0.9em;">${item.desc || ''}</div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                                <strong>${item.preco}</strong>
                                <button class="add-cart-btn" data-name="${item.nome}" data-price="${item.preco}" style="background: #28a745; border: none; color: white; padding: 4px 10px; border-radius: 15px; cursor: pointer; font-size: 0.8em;">Eu quero! 😋</button>
                            </div>
                         </div>`;
            });

            html += `<div style="margin-top: 15px; text-align: center;">
                        <button class="back-to-menu-btn" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 0.9em;">Ver Cardápio Completo</button>
                     </div>`;

            addMessage(html, 'bot');

        } catch (error) {
            console.error("Erro ao buscar destaques", error);
            addMessage("Tive um probleminha para consultar os destaques. Mas você pode ver o cardápio completo!", 'bot');
            showMenuCategories();
        }
    }

    // Buscar e Exibir Cardápio da API
    async function fetchAndShowMenu(filter = null) {
        try {
            addMessage("Buscando as melhores opções para você... 😋", 'bot');

            const response = await fetch('/api/cardapio');
            if (!response.ok) throw new Error('Erro na API');

            const menu = await response.json();

            if (Object.keys(menu).length === 0) {
                addMessage("O cardápio parece estar vazio no momento. 😕 Tente novamente mais tarde.", 'bot');
                return;
            }

            let html = "<strong>📋 Aqui está:</strong><br>";

            // Define quais categorias exibir
            let keysToShow = [];
            if (Array.isArray(filter)) keysToShow = filter;
            else if (filter) keysToShow = [filter];
            else keysToShow = Object.keys(menu); // Mostra tudo se não houver filtro

            for (const category of keysToShow) {
                const items = menu[category];
                if (!items) continue;

                html += `<div style="margin-top: 15px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 5px; margin-bottom: 5px;">
                            <strong style="color: #ffc107; text-transform: uppercase; font-size: 0.9em;">${category}</strong>
                         </div>`;
                items.forEach(item => {
                    // Ignora itens invisíveis
                    if (item.visivel === false) return;

                    const isFav = isFavorite(item.nome);
                    const star = isFav ? '⭐' : '☆';
                    const starColor = isFav ? '#ffc107' : 'rgba(255,255,255,0.5)';

                    // Lógica de Esgotado
                    const isSoldOut = item.esgotado === true;
                    let actionBtn = '';

                    if (isSoldOut) {
                        actionBtn = `<span style="color: #dc3545; font-weight: bold; font-size: 0.75em; border: 1px solid #dc3545; padding: 2px 6px; border-radius: 10px; white-space: nowrap;">Esgotado</span>`;
                    } else {
                        actionBtn = `<button class="add-cart-btn" data-name="${item.nome}" data-price="${item.preco}" style="background: #28a745; border: none; color: white; width: 28px; height: 28px; border-radius: 50%; cursor: pointer; font-weight: bold; flex-shrink: 0;">+</button>`;
                    }

                    html += `<div style="margin-bottom: 8px; padding: 4px 0; display: flex; align-items: center; justify-content: space-between; ${isSoldOut ? 'opacity: 0.6;' : ''}">
                                <div style="flex: 1;">
                                    <div style="display: flex; justify-content: space-between;"><strong>${item.nome}</strong> <span style="margin-left: 5px;">${item.preco}</span></div>
                                    <div style="font-size: 0.85em; opacity: 0.8; line-height: 1.2;">${item.desc}</div>
                                </div>
                                <div style="display: flex; gap: 5px; align-items: center; margin-left: 8px;">
                                    <button class="fav-btn" data-name="${item.nome}" data-price="${item.preco}" data-desc="${item.desc}" style="background: transparent; border: none; cursor: pointer; font-size: 1.4em; color: ${starColor}; padding: 0;">${star}</button>
                                    ${actionBtn}
                                </div>
                             </div>`;
                });
            }

            html += `<div style="margin-top: 15px; text-align: center;">
                        <button class="back-to-menu-btn" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 0.9em; transition: background 0.2s;">⬅ Voltar ao Menu</button>
                     </div>`;

            addMessage(html, 'bot');
        } catch (error) {
            console.error("Erro ao buscar cardápio", error);
            addMessage("Desculpe, tive um problema ao carregar o cardápio. 😕 Mas você pode ver na aba 'Cardápio' do site!", 'bot');
        }
    }

    // Carrega conhecimento
    fetch('/static/js/ai_knowledge.json')
        .then(response => response.json())
        .then(data => {
            knowledgeBase = data.keywords;
            fallbackResponse = data.fallback;
            input.disabled = false;
            sendBtn.disabled = false;
            input.placeholder = "Pergunte sobre pizzas, rodízio...";
        })
        .catch(err => console.error("Erro ao carregar IA", err));

    // Toggle Chat
    const toggleChat = () => {
        widget.classList.toggle('open');
        if (widget.classList.contains('open')) {
            if (badge) badge.style.display = 'none';
            input.focus();
        }
    };

    toggleBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    // Event listener para botões dinâmicos (como "Voltar ao Menu")
    messagesContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('back-to-menu-btn')) {
            showMenuCategories("Sem problemas! Vamos escolher outra coisa. 😉");
        }
        if (e.target.classList.contains('add-cart-btn')) {
            const name = e.target.getAttribute('data-name');
            const price = e.target.getAttribute('data-price');
            addToCart(name, price);
        }
        if (e.target.classList.contains('show-drinks-btn')) {
            fetchAndShowMenu('Bebidas');
        }
        if (e.target.classList.contains('finalize-order-btn')) {
            finalizeOrder();
        }
        if (e.target.classList.contains('view-cart-btn')) {
            showCart();
        }
        if (e.target.classList.contains('remove-cart-item-btn')) {
            const index = parseInt(e.target.getAttribute('data-index'));
            removeFromCart(index);
        }
        if (e.target.classList.contains('fav-btn')) {
            const btn = e.target;
            const name = btn.getAttribute('data-name');
            const price = btn.getAttribute('data-price');
            const desc = btn.getAttribute('data-desc');
            toggleFavorite(name, price, desc);
            const isFav = isFavorite(name);
            btn.textContent = isFav ? '⭐' : '☆';
            btn.style.color = isFav ? '#ffc107' : 'rgba(255,255,255,0.5)';
        }
        if (e.target.classList.contains('rate-star')) {
            const val = e.target.getAttribute('data-val');
            let stars = '★'.repeat(val);
            addMessage(`Obrigado pela avaliação! ${stars}<br>Ficamos felizes em atender você.`, 'bot');
            const container = e.target.closest('.rating-container');
            if (container) container.remove();
        }
        if (e.target.classList.contains('chat-option-btn')) {
            const val = e.target.getAttribute('data-val');
            input.value = val;
            handleUserMessage();
        }
    });

    // Saudação Inicial
    function getGreeting() {
        const status = getStoreStatus();
        if (status.isOpen) return `Boa noite! A chapa está quente 🔥.<br>🕒 Tempo médio de espera: <strong>${currentWaitTime}</strong>.<br>O que manda hoje?`;
        return `Olá! ${status.message} Posso ajudar com o cardápio ou agendar um pedido?`;
    }

    if (messagesContainer) {
        messagesContainer.innerHTML = `<div class="ai-message bot">${getGreeting()} Sou a Assistente Virtual.</div>`;
    }

    clearBtn.addEventListener('click', () => {
        messagesContainer.innerHTML = `<div class="ai-message bot">${getGreeting()}</div>`;
    });

    // Mascara para CEP
    input.addEventListener('input', function (e) {
        if (checkoutState === 'cep') {
            const val = e.target.value;
            // Só aplica máscara se começar com número (CEP)
            if (/^\d/.test(val)) {
                let clean = val.replace(/\D/g, '');
                if (clean.length > 8) clean = clean.substring(0, 8);
                if (clean.length > 5) {
                    e.target.value = clean.substring(0, 5) + '-' + clean.substring(5);
                } else {
                    e.target.value = clean;
                }
            }
        }
    });

    // Adicionar Mensagem
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `ai-message ${sender}`;
        div.innerHTML = text;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Processar Mensagem
    async function handleUserMessage() {
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, 'user');
        input.value = '';

        // Indicador de digitação
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'typing-indicator';
        loadingDiv.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // --- Lógica de Checkout (Máquina de Estados) ---
        if (checkoutState) {
            loadingDiv.remove();

            // 1. Escolha do Método
            if (checkoutState === 'method') {
                if (text.match(/1|entrega/i)) {
                    orderData.method = 'Entrega';
                    checkoutState = 'cep';
                    addMessage("Ótimo! Por favor, digite o **CEP** para entrega:", 'bot');
                } else if (text.match(/2|retirada|buscar/i)) {
                    orderData.method = 'Retirada';

                    const savedName = localStorage.getItem('vts_user_name');
                    const savedPhone = localStorage.getItem('vts_user_phone');
                    if (savedName && savedPhone) {
                        checkoutState = 'check_saved';
                        addMessage(`Encontrei seus dados: <strong>${savedName}</strong> (${savedPhone}).<br>Deseja usá-los?<br>
                            <button class="chat-option-btn" data-val="Sim" style="background: #28a745; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Sim</button>
                            <button class="chat-option-btn" data-val="Não" style="background: #dc3545; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Não</button>`, 'bot');
                    } else {
                        checkoutState = 'name';
                        addMessage("Certo! Qual é o seu **nome**?", 'bot');
                    }
                } else {
                    addMessage("Por favor, escolha 1 para Entrega ou 2 para Retirada.", 'bot');
                }
                return;
            }

            // 2. Verificação de CEP (se Entrega)
            // 2. Verificação de CEP ou Rua
            if (checkoutState === 'cep') {
                // Se parece CEP (números), valida formato
                if (/^\d/.test(text)) {
                    const cepClean = text.replace(/\D/g, '');
                    if (cepClean.length !== 8) {
                        addMessage("CEP inválido. Use o formato 00000-000 ou digite o nome da rua.", 'bot');
                        return;
                    }
                    // Processa CEP
                    try {
                        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&countrycodes=br&limit=1&postalcode=${cepClean}&addressdetails=1`);
                        const data = await response.json();
                        await handleLocationResult(data, text);
                    } catch (e) { handleLocationError(); }
                    return;
                }

                // Se é Texto -> Busca por Rua (Bairro próximo)
                try {
                    addMessage(`🔎 Buscando rua "${text}"...`, 'bot');
                    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&countrycodes=br&limit=3&q=${encodeURIComponent(text + ", SP")}&addressdetails=1`);
                    const data = await response.json();
                    await handleLocationResult(data, text, true);
                } catch (e) { handleLocationError(); }
                return;
            }

            async function handleLocationResult(data, inputText, isStreetSearch = false) {
                if (!data || data.length === 0) {
                    addMessage(isStreetSearch
                        ? "Não encontrei essa rua próxima. 😕 Tente o CEP ou o nome do bairro."
                        : "Não encontrei esse CEP. 😕 Tente o nome da rua.", 'bot');
                    return;
                }

                const location = data[0];
                const userLat = parseFloat(location.lat);
                const userLon = parseFloat(location.lon);
                let minDistance = Infinity;
                let nearestUnit = null;

                units.forEach(unit => {
                    const dist = calculateDistance(userLat, userLon, unit.lat, unit.lon);
                    if (dist < minDistance) {
                        minDistance = dist;
                        nearestUnit = unit;
                    }
                });

                const address = location.address || {};
                const street = address.road || address.street || (isStreetSearch ? inputText : "Rua identificada");
                const neighborhood = address.suburb || address.neighbourhood || "";

                if (minDistance <= 6) {
                    currentUnit = nearestUnit;
                    orderData.cep = isStreetSearch ? "Não informado" : inputText;
                    orderData.fee = calculateDeliveryFee(minDistance);
                    orderData.street = street + (neighborhood ? ` - ${neighborhood}` : "");

                    checkoutState = 'address_number';
                    addMessage(`Entregamos sim! (Distância: ${minDistance.toFixed(1)}km)<br>📍 Local: <strong>${orderData.street}</strong><br>Taxa: ${orderData.fee}<br><br>Por favor, digite o <strong>número e complemento</strong>.`, 'bot');
                } else {
                    addMessage(`Poxa, <strong>${street}</strong> fica longe (${minDistance.toFixed(1)}km). Limite: 6km. 😕<br>Deseja mudar para **Retirada**?<br>
                        <button class="chat-option-btn" data-val="Sim" style="background: #28a745; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Sim</button>
                        <button class="chat-option-btn" data-val="Não" style="background: #dc3545; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Não</button>`, 'bot');
                    checkoutState = 'switch_method';
                }
            }

            function handleLocationError() {
                addMessage("Erro ao verificar localização. Tente novamente.", 'bot');
            }

            // 2.5 Número e Complemento
            if (checkoutState === 'address_number') {
                // Validação: Verifica se tem pelo menos um dígito
                if (!/\d/.test(text)) {
                    addMessage("Parece que faltou o número. 🏠 Por favor, digite o **número** do endereço (ex: 123).", 'bot');
                    return;
                }
                orderData.number_complement = text;

                const savedName = localStorage.getItem('vts_user_name');
                const savedPhone = localStorage.getItem('vts_user_phone');
                if (savedName && savedPhone) {
                    checkoutState = 'check_saved';
                    addMessage(`Anotado! 📝<br>Encontrei seus dados: <strong>${savedName}</strong> (${savedPhone}).<br>Deseja usá-los?<br>
                        <button class="chat-option-btn" data-val="Sim" style="background: #28a745; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Sim</button>
                        <button class="chat-option-btn" data-val="Não" style="background: #dc3545; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Não</button>`, 'bot');
                } else {
                    checkoutState = 'name';
                    addMessage(`Anotado! 📝<br>Qual é o seu **nome**?`, 'bot');
                }
                return;
            }

            // 2.1 Alternativa se CEP for longe
            if (checkoutState === 'switch_method') {
                if (text.match(/sim|s|quero/i)) {
                    orderData.method = 'Retirada';
                    orderData.fee = 'R$ 0,00';

                    const savedName = localStorage.getItem('vts_user_name');
                    const savedPhone = localStorage.getItem('vts_user_phone');
                    if (savedName && savedPhone) {
                        checkoutState = 'check_saved';
                        addMessage(`Combinado! Retirada na loja.<br>Encontrei seus dados: <strong>${savedName}</strong> (${savedPhone}).<br>Deseja usá-los?<br>
                            <button class="chat-option-btn" data-val="Sim" style="background: #28a745; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Sim</button>
                            <button class="chat-option-btn" data-val="Não" style="background: #dc3545; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">Não</button>`, 'bot');
                    } else {
                        checkoutState = 'name';
                        addMessage("Combinado! Retirada na loja. Qual é o seu **nome**?", 'bot');
                    }
                } else {
                    checkoutState = null;
                    addMessage("Tudo bem. Pedido cancelado. Se mudar de ideia, estou aqui!", 'bot');
                }
                return;
            }

            // 2.2 Verificar dados salvos
            if (checkoutState === 'check_saved') {
                if (text.match(/sim|s|pode|quero/i)) {
                    orderData.name = localStorage.getItem('vts_user_name');
                    orderData.phone = localStorage.getItem('vts_user_phone');
                    checkoutState = 'obs';
                    addMessage(`Dados confirmados! ✅<br>Alguma **observação** para o pedido? (Ex: sem cebola, troco para 50).<br>Se não tiver, digite 'não'.`, 'bot');
                } else {
                    checkoutState = 'name';
                    addMessage("Sem problemas. Qual é o seu **nome**?", 'bot');
                }
                return;
            }

            // 3. Nome
            if (checkoutState === 'name') {
                orderData.name = text;
                checkoutState = 'phone';
                addMessage("Prazer, " + text + "! Agora, qual seu **celular/WhatsApp** (com DDD)?", 'bot');
                return;
            }

            // 4. Telefone (com validação)
            if (checkoutState === 'phone') {
                const phoneClean = text.replace(/\D/g, '');
                if (phoneClean.length < 10) {
                    addMessage("O número parece curto demais. 📱 Por favor, digite o DDD + Número (mínimo 10 dígitos).", 'bot');
                    return;
                }
                orderData.phone = text;
                checkoutState = 'coupon';
                addMessage(`Anotado! 📱<br>Você tem algum **cupom de desconto**? Digite o código ou clique abaixo:<br>
                    <button class="chat-option-btn" data-val="Não" style="background: #6c757d; border: none; color: white; padding: 6px 12px; margin-top: 5px; border-radius: 15px; cursor: pointer;">Não tenho cupom</button>`, 'bot');
                return;
            }

            // 5. Cupom
            if (checkoutState === 'coupon') {
                if (text.match(/^n(ão|ao)$/i)) {
                    checkoutState = 'payment';
                    addMessage(`Tudo bem! Como você prefere **pagar**?<br>
                        <button class="chat-option-btn" data-val="Cartão" style="background: #0d6efd; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">💳 Cartão</button>
                        <button class="chat-option-btn" data-val="Dinheiro" style="background: #198754; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">💵 Dinheiro</button>
                        <button class="chat-option-btn" data-val="Pix" style="background: #0dcaf0; border: none; color: black; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">💠 Pix</button>`, 'bot');
                } else {
                    // Validar Cupom na API
                    try {
                        const response = await fetch('/api/cupom/validar', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ codigo: text })
                        });
                        const data = await response.json();

                        if (data.valid) {
                            orderData.discount = data;
                            checkoutState = 'payment';
                            addMessage(`🎉 Cupom <strong>${data.codigo}</strong> aplicado com sucesso!<br>Como você prefere **pagar**?<br>
                                <button class="chat-option-btn" data-val="Cartão" style="background: #0d6efd; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">💳 Cartão</button>
                                <button class="chat-option-btn" data-val="Dinheiro" style="background: #198754; border: none; color: white; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">💵 Dinheiro</button>
                                <button class="chat-option-btn" data-val="Pix" style="background: #0dcaf0; border: none; color: black; padding: 6px 12px; margin: 5px; border-radius: 15px; cursor: pointer;">💠 Pix</button>`, 'bot');
                        } else {
                            addMessage(`❌ ${data.message}<br>Tente outro código ou clique abaixo:<br>
                                <button class="chat-option-btn" data-val="Não" style="background: #6c757d; border: none; color: white; padding: 6px 12px; margin-top: 5px; border-radius: 15px; cursor: pointer;">Continuar sem cupom</button>`, 'bot');
                        }
                    } catch (e) {
                        addMessage("Erro ao validar cupom. Digite 'não' para continuar.", 'bot');
                    }
                }
                return;
            }

            // 5.5 Pagamento
            if (checkoutState === 'payment') {
                const lower = text.toLowerCase();
                if (lower.includes('cart') || lower.includes('crédito') || lower.includes('débito')) {
                    orderData.paymentMethod = 'Cartão (Levamos maquininha)';
                } else if (lower.includes('pix')) {
                    orderData.paymentMethod = 'Pix (Chave na entrega ou QR Code)';
                } else if (lower.includes('dinheiro') || lower.includes('nota') || lower.includes('cedula')) {
                    orderData.paymentMethod = 'Dinheiro';
                    checkoutState = 'payment_change';
                    addMessage("Certo! Vai precisar de **troco** para quanto? (Digite o valor ou 'não')", 'bot');
                    return;
                } else {
                    addMessage("Não entendi. Escolha: Cartão, Dinheiro ou Pix.", 'bot');
                    return;
                }
                // Se não for dinheiro, vai pro obs
                checkoutState = 'obs';
                addMessage(`Ok, ${orderData.paymentMethod}.<br>Alguma **observação** para o pedido? (Ex: sem cebola).<br>
                    <button class="chat-option-btn" data-val="Não" style="background: #6c757d; border: none; color: white; padding: 6px 12px; margin-top: 5px; border-radius: 15px; cursor: pointer;">Sem observações</button>`, 'bot');
                return;
            }

            // 5.6 Troco
            if (checkoutState === 'payment_change') {
                if (text.match(/^n(ão|ao)$/i)) {
                    orderData.change = 'Sem troco';
                } else {
                    orderData.change = text;
                }
                checkoutState = 'obs';
                addMessage(`Anotado. Alguma **observação** final para o pedido?<br>
                    <button class="chat-option-btn" data-val="Não" style="background: #6c757d; border: none; color: white; padding: 6px 12px; margin-top: 5px; border-radius: 15px; cursor: pointer;">Sem observações</button>`, 'bot');
                return;
            }

            // 6. Observações e Finalização
            if (checkoutState === 'obs') {
                orderData.obs = text.match(/^n(ão|ao)$/i) ? '' : text;
                finishCheckout();
                return;
            }
        }

        // Verifica se é um CEP (XXXXX-XXX ou XXXXXXXX)
        const cepMatch = text.match(/\b\d{5}-?\d{3}\b/);
        if (cepMatch) {
            const cep = cepMatch[0].replace('-', '');
            const response = await processDeliveryCheck(cep);
            loadingDiv.remove();
            addMessage(response, 'bot');
            return;
        }

        // Verifica se está aguardando o bairro (Contexto)
        if (awaitingNeighborhood) {
            awaitingNeighborhood = false;
            const response = await processNeighborhoodCheck(text);
            loadingDiv.remove();
            addMessage(response, 'bot');
            return;
        }

        // Verifica se está aguardando escolha do tipo de comida
        if (awaitingMenuCategory) {
            const lowerText = text.toLowerCase();
            let filter = undefined;

            if (text === '2' || lowerText.includes('churrasco') || lowerText.includes('espeto')) filter = 'Churrasco';
            else if (text === '3' || lowerText.includes('hamburguer') || lowerText.includes('burger') || lowerText.includes('lanche')) filter = 'Hambúrgueres';
            else if (text === '4' || lowerText.includes('marmita') || lowerText.includes('almoço')) filter = 'Marmitex';
            else if (text === '5' || lowerText.includes('bebida') || lowerText.includes('refri')) filter = 'Bebidas';
            else if (text === '6' || lowerText.includes('tudo') || lowerText.includes('completo') || lowerText.includes('todos')) filter = null;
            else if (text === '7' || lowerText.includes('favorito')) {
                awaitingMenuCategory = false;
                loadingDiv.remove();
                showFavorites();
                return;
            }
            else if (lowerText.includes('doce') || lowerText.includes('sobremesa')) filter = 'Pizzas Doces';
            else if (lowerText.includes('salgada') || lowerText.includes('tradicional')) filter = 'Pizzas Salgadas';
            else if (text === '1' || lowerText.includes('pizza')) filter = ['Pizzas Salgadas', 'Pizzas Doces']; // Mostra ambas

            if (filter !== undefined) {
                awaitingMenuCategory = false;
                loadingDiv.remove();
                await fetchAndShowMenu(filter);
                return;
            } else {
                // Se não entendeu a categoria, mantém o estado e pergunta de novo
                loadingDiv.remove();
                addMessage("Não entendi. 😕 Digite o número ou nome:<br>1. Pizzas<br>2. Churrasco<br>3. Hambúrgueres<br>4. Marmitex<br>5. Bebidas<br>6. Ver Tudo<br>7. Favoritos", 'bot');
                return;
            }
        }

        // Verifica solicitação de finalizar pedido
        if (text.match(/\b(finalizar|fechar|pedido|carrinho|comprar)\b/i)) {
            loadingDiv.remove();
            finalizeOrder();
            return;
        }

        // Verifica solicitação de Pontos de Fidelidade
        if (text.match(/\b(pontos|fidelidade|saldo)\b/i)) {
            loadingDiv.remove();
            const savedPhone = localStorage.getItem('vts_user_phone');

            if (savedPhone) {
                fetch('/api/fidelidade/pontos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone: savedPhone })
                })
                    .then(r => r.json())
                    .then(data => {
                        addMessage(`🏆 Você tem <strong>${data.pontos} pontos</strong> no Clube Colonial!<br>Continue pedindo para acumular mais.`, 'bot');
                    });
            } else {
                addMessage("Para consultar seus pontos, preciso saber quem é você. Faça seu primeiro pedido para começar a pontuar! 🍕", 'bot');
            }
            return;
        }

        // Verifica solicitação de Sugestão (IA)
        if (text.match(/o que tem de bom|sugestão|indicação|recomenda|destaque|sugere/i)) {
            loadingDiv.remove();
            suggestHighlights();
            return;
        }

        // Verifica solicitação de Cardápio (Integração API)
        if (text.match(/\b(cardápio|menu|opções|fome)\b/i)) {
            loadingDiv.remove();
            showMenuCategories();
            return;
        }

        setTimeout(() => {
            loadingDiv.remove();
            let response = fallbackResponse;

            // Lógica de busca
            for (const key in knowledgeBase) {
                try {
                    const regex = new RegExp(key, 'i');
                    if (regex.test(text)) {
                        const potential = knowledgeBase[key];
                        // Se for array, escolhe aleatório. Se for objeto (ex: resposta variante), pega 'default'.
                        response = Array.isArray(potential) ? potential[Math.floor(Math.random() * potential.length)] : potential;
                        if (typeof response === 'object' && response !== null && !Array.isArray(response)) response = response.default || JSON.stringify(response);
                        break;
                    }
                } catch (e) { }
            }

            addMessage(response, 'bot');
        }, 800);
    }

    sendBtn.addEventListener('click', handleUserMessage);
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleUserMessage(); });

    // Chips de Sugestão
    document.querySelectorAll('.ai-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            input.value = chip.textContent;
            handleUserMessage();
        });
    });
}

function initInactivityFeatures() {
    const idleLimit = 15000; // 15 segundos de inatividade para ativar
    let idleTimer;
    let alternationInterval;
    const aiBtn = document.getElementById('ai-toggle-btn');
    const waBtn = document.getElementById('whatsapp-floating');
    const aiContainer = document.getElementById('ai-widget-container');

    // Injeta o Tooltip do WhatsApp se não existir
    let waBubble = document.getElementById('whatsapp-cta-bubble');
    if (waBtn && !waBubble) {
        waBubble = document.createElement('span');
        waBubble.id = 'whatsapp-cta-bubble';
        waBubble.textContent = 'Peça pelo Zap';
        waBtn.appendChild(waBubble);
    }

    // Injeta o Tooltip da IA se não existir
    let aiBubble = document.getElementById('ai-cta-bubble');
    if (aiContainer && !aiBubble) {
        aiBubble = document.createElement('div');
        aiBubble.id = 'ai-cta-bubble';
        aiBubble.textContent = 'Fale com a Atendente';
        aiContainer.appendChild(aiBubble);
    } else if (aiBubble) {
        aiBubble.textContent = 'Fale com a Atendente';
    }

    function playAttentionSound() {
        // Verifica se a aba está visível (não toca se estiver minimizada/oculta)
        if (document.hidden) return;

        // Verifica se o som está desativado pelo usuário
        if (localStorage.getItem('site_sound_muted') === 'true') return;

        // Som de "Assobio" (Slide de frequência)
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;

            const ctx = new AudioContext();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.connect(gain);
            gain.connect(ctx.destination);

            const now = ctx.currentTime;
            osc.type = 'sine'; // Onda senoidal pura
            osc.frequency.setValueAtTime(900, now); // Começa em 900Hz
            osc.frequency.exponentialRampToValueAtTime(2200, now + 0.2); // Sobe rápido para 2200Hz (Efeito Assobio)

            gain.gain.setValueAtTime(0.05, now); // Volume baixo
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3); // Fade out

            osc.start(now);
            osc.stop(now + 0.3);
        } catch (e) {
            console.warn("Erro ao tocar som:", e);
        }
    }

    function showAttention() {
        if (aiBtn) aiBtn.classList.add('attention-seeker');
        if (waBtn) waBtn.classList.add('attention-seeker');

        playAttentionSound();

        // Lógica de alternância dos tooltips
        let showAi = true;
        const flashTooltip = () => {
            // Garante que ambos comecem ocultos
            if (aiBubble) aiBubble.classList.remove('tooltip-visible');
            if (waBubble) waBubble.classList.remove('tooltip-visible');

            // Escolhe qual mostrar
            const target = showAi ? aiBubble : waBubble;
            if (target) {
                target.classList.add('tooltip-visible');
                // Esconde após 10 segundos
                setTimeout(() => {
                    target.classList.remove('tooltip-visible');
                }, 10000);
            }
            showAi = !showAi;
        };

        flashTooltip(); // Mostra o primeiro imediatamente
        alternationInterval = setInterval(flashTooltip, 120000); // Alterna a cada 2 minutos
    }

    function resetAttention() {
        if (aiBtn) aiBtn.classList.remove('attention-seeker');
        if (waBtn) waBtn.classList.remove('attention-seeker');

        // Remove visibilidade forçada
        if (aiBubble) aiBubble.classList.remove('tooltip-visible');
        if (waBubble) waBubble.classList.remove('tooltip-visible');

        clearInterval(alternationInterval);
        clearTimeout(idleTimer);
        idleTimer = setTimeout(showAttention, idleLimit);
    }

    // Eventos que resetam o timer (interação do usuário)
    const events = ['mousemove', 'keydown', 'scroll', 'click', 'touchstart'];
    events.forEach(evt => {
        document.addEventListener(evt, resetAttention, { passive: true });
    });

    // Inicia o timer
    resetAttention();
}

function initSoundSettings() {
    // Cria o botão flutuante de som
    const btn = document.createElement('button');
    btn.id = 'sound-toggle-btn';

    // Estilos inline para garantir posicionamento (Canto Inferior Esquerdo)
    Object.assign(btn.style, {
        position: 'fixed',
        left: '20px',
        bottom: '20px',
        zIndex: '1080',
        width: '45px',
        height: '45px',
        borderRadius: '50%',
        border: 'none',
        background: '#0f172a', // Cor escura do tema
        color: '#ffc107',      // Cor amarela do tema
        fontSize: '1.2rem',
        cursor: 'pointer',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.3s ease'
    });

    const updateState = () => {
        const isMuted = localStorage.getItem('site_sound_muted') === 'true';
        btn.innerHTML = isMuted ? '🔇' : '🔊';
        btn.title = isMuted ? 'Ativar Sons' : 'Desativar Sons';
        btn.style.opacity = isMuted ? '0.7' : '1';
    };

    btn.addEventListener('click', () => {
        const isMuted = localStorage.getItem('site_sound_muted') === 'true';
        localStorage.setItem('site_sound_muted', !isMuted);
        updateState();
    });

    // Efeito Hover
    btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.1)');
    btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1)');

    updateState();
    document.body.appendChild(btn);
}

function playWelcomeMessage() {
    // Verifica se o som está desativado ou se a aba está oculta
    if (localStorage.getItem('site_sound_muted') === 'true' || document.hidden) return;

    // Verifica se já tocou nesta sessão
    if (sessionStorage.getItem('welcome_audio_played')) return;

    if ('speechSynthesis' in window) {
        // Aguarda carregar config (via fetch ou timeout)
        let attempts = 0;
        const checkConfig = setInterval(() => {
            attempts++;
            if (window.siteConfig || attempts > 20) { // 2s max wait
                clearInterval(checkConfig);
                speakWelcome();
            }
        }, 100);
    }
}

function speakWelcome() {
    try {
        const utterance = new SpeechSynthesisUtterance();
        utterance.lang = 'pt-BR';
        utterance.rate = 1.1;
        utterance.volume = 0.8;

        // Seleção de Voz Baseada na Config
        const voices = window.speechSynthesis.getVoices();
        let selectedVoice = null;
        const gender = (window.siteConfig && window.siteConfig.voice_gender) || 'female';

        // Preferências conhecidas
        let assistantName = "Val";
        if (gender === 'female') {
            selectedVoice = voices.find(v => v.lang.includes('pt-BR') && (v.name.includes('Google') || v.name.includes('Luciana') || v.name.includes('Female')));
        } else {
            selectedVoice = voices.find(v => v.lang.includes('pt-BR') && (v.name.includes('Daniel') || v.name.includes('Male')));
            assistantName = "Giovani";
        }

        // Atualiza Nome na UI
        const nameEl = document.getElementById('ai-assistant-name');
        if (nameEl) nameEl.innerText = assistantName;

        // Fallback genérico pt-BR
        if (!selectedVoice) selectedVoice = voices.find(v => v.lang.includes('pt-BR'));

        if (selectedVoice) utterance.voice = selectedVoice;

        const text = `Olá! Bem-vindo à Pizzaria Colonial. Eu sou ${assistantName === 'Val' ? 'a Val' : 'o Giovani'}, seu assistente virtual.`;
        utterance.text = text;

        window.speechSynthesis.speak(utterance);
        sessionStorage.setItem('welcome_audio_played', 'true');
    } catch (e) {
        console.warn("Autoplay de áudio bloqueado:", e);
    }
}