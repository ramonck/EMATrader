# LIGHTER · Lighter para principiantes

## Descripción y costes

Lighter es un protocolo para operar contratos perpetuos en el ecosistema Ethereum. Un perpetuo sigue el precio de un activo, como BTC, sin fecha de vencimiento. EMA Trader usa la API de Lighter para consultar la cuenta y ejecutar órdenes. Las comisiones, el spread y la financiación afectan al resultado. Una posición apalancada puede liquidarse. [Preguntas frecuentes de Lighter](https://lighter.xyz/faq) · [Tarifas oficiales](https://docs.lighter.xyz/trading/trading-fees)

Velas públicas → banda EMA de 15 minutos → señal → orden firmada localmente → confirmación de Lighter.

## Depositar en Lighter

USDC es una moneda estable diseñada para seguir el valor del dólar estadounidense. La red es la vía por la que se transfieren los tokens. Una dirección que empieza por `0x` puede existir en varias redes, así que revisa también cuál has seleccionado. [USDC de Circle](https://www.circle.com/usdc)

1. Abre [app.lighter.xyz](https://app.lighter.xyz/), comprueba tu elegibilidad en los [términos de Lighter](https://lighter.xyz/terms) y conecta una billetera que controles.
2. Abre **Depositar** y selecciona USDC si está disponible. Revisa las redes de origen y rutas ofrecidas. La pantalla indica si la ruta empieza en tu billetera, si requiere aprobar una transacción o si genera una dirección de depósito.
3. Antes de comprar o retirar, comprueba que el activo y la red coincidan en ambos extremos. Si la ruta empieza en tu billetera, retira de la plataforma a la dirección de tu propia billetera en esa red. Después revisa y confirma el depósito en la interfaz oficial. Si la pantalla genera una dirección de depósito, sigue las instrucciones de esa ruta.
4. En Arbitrum One, **USDC nativo** y **USDC.e** son tokens distintos. Verifica cuál exige la ruta. Si vas a firmar una transacción en la billetera, comprueba que tienes saldo para la comisión de red. Empieza con un envío pequeño que supere el mínimo indicado. [Redes y contratos de USDC](https://developers.circle.com/stablecoins/usdc-contract-addresses) · [Arbitrum One](https://docs.arbitrum.io/arbitrum-bridge/quickstart)
5. Confirma el ingreso en el historial de depósitos de Lighter y revisa el saldo de la cuenta. Ver USDC en tu billetera significa que llegó el retiro de la plataforma. El saldo de Lighter aparece después del depósito.

## Comprar USDC con moneda local

- **México.** Desde la sección de depósitos de tu plataforma, obtén la CLABE que te indique. Haz una transferencia SPEI desde una cuenta a tu nombre. Cuando se acredite el saldo, verifica que puedas comprar USDC y retirarlo por la red que necesitas. [SPEI en Bitso](https://support.bitso.com/hc/es-mx/articles/4415147781012-C%C3%B3mo-hacer-una-transferencia-SPEI-en-pesos-mexicanos)
- **Argentina.** Usa el CVU de depósito que muestre tu cuenta y envía ARS desde tu banco o aplicación de pagos a tu nombre. [Depósitos en Bitso Argentina](https://support.bitso.com/hc/es-ar/articles/51158963807124--C%C3%B3mo-deposito-pesos-argentinos-ARS)
- **Colombia.** Usa el método de depósito en COP que aparezca en tu cuenta. Bitso documenta el flujo vía Bancolombia. [Depósitos en Bitso Colombia](https://support.bitso.com/hc/es-co/articles/53399222316436-C%C3%B3mo-depositar-pesos-colombianos-COP)
- **Otros países.** Elige una plataforma disponible en tu país, deposita tu moneda local y compra USDC. Comprueba que puedas retirar el token por una red aceptada por la ruta de Lighter. Revisa el mínimo, la comisión y el importe que llegará. [Redes para retiros de Bitso](https://support.bitso.com/hc/en-us/articles/4419901801748-Which-network-to-use-to-deposit-or-withdraw-crypto-on-Bitso)

## Conectar EMA Trader

1. En la cuenta o subcuenta que quieras seguir, anota el **índice de cuenta** y crea una clave API vinculada a ella. Anota también el **índice de clave**. El primero identifica la cuenta y el segundo, la credencial.
2. En EMA Trader, abre **Configuración → Órdenes** y desbloquea la bóveda. Selecciona **Mainnet** para la cuenta real. Introduce el índice de cuenta y elige **Solo seguir la cuenta** para comprobar la posición. Comprueba el saldo disponible en la interfaz de Lighter.
3. Para probar órdenes con fondos de prueba, utiliza Testnet y una clave creada en esa red. Para activar órdenes, introduce la clave privada de API, el margen base y el apalancamiento en el programa. Guarda la frase de recuperación de la billetera fuera de la aplicación.
4. Mantén EMA Trader abierto para vigilar y ejecutar señales. Puedes cerrar el navegador después de configurar la cuenta.

[Abrir Testnet](https://testnet.app.lighter.xyz/) · [ORDERS](ORDERS.md) · [SUBACCOUNTS](SUBACCOUNTS.md) · [DATA](DATA.md)
