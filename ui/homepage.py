import streamlit as st
from html import escape
from urllib.parse import urlencode

from utils.common import query_param as _query_param
from utils.data import load_live_price
from utils.i18n import t


QUICK_TOPIC_KEYS = {"trending", "best_etfs", "dividend", "ai", "undervalued"}


def _set_query_param(name: str, value: str | None) -> None:
    current = _query_param(st.query_params, name)
    if value:
        if current != value:
            st.query_params[name] = value
    elif current is not None:
        st.query_params.pop(name, None)


def set_quick_topic(topic: str) -> None:
    st.session_state.quick_topic = topic
    st.session_state.topic_url_value = topic if topic != "trending" else None
    st.session_state.search_results = []
    st.session_state.search_no_results = None
    st.session_state.reset_search_query = True
    st.session_state.last_search_query = ""
    st.query_params.pop("q", None)
    st.query_params.pop("stock", None)
    st.query_params.pop("company", None)
    _set_query_param("topic", topic if topic != "trending" else None)
    st.rerun()


COUNTRY_MARKETS = {
    "United States": {
        "label": "🇺🇸 United States",
        "indexes": [
            ("S&P 500", "^GSPC", "USD"),
            ("NASDAQ", "^IXIC", "USD"),
        ],
        "stocks": [
            ("Apple", "AAPL", "USD"),
            ("Nvidia", "NVDA", "USD"),
            ("Microsoft", "MSFT", "USD"),
            ("Tesla", "TSLA", "USD"),
        ],
    },
    "India": {
        "label": "🇮🇳 India",
        "indexes": [
            ("NIFTY 50", "^NSEI", "INR"),
            ("SENSEX", "^BSESN", "INR"),
        ],
        "stocks": [
            ("Reliance", "RELIANCE.NS", "INR"),
            ("TCS", "TCS.NS", "INR"),
            ("Infosys", "INFY.NS", "INR"),
            ("HDFC Bank", "HDFCBANK.NS", "INR"),
        ],
    },
    "United Kingdom": {
        "label": "🇬🇧 United Kingdom",
        "indexes": [
            ("FTSE 100", "^FTSE", "GBp"),
            ("FTSE 250", "^FTMC", "GBp"),
        ],
        "stocks": [
            ("AstraZeneca", "AZN.L", "GBp"),
            ("Shell", "SHEL.L", "GBp"),
            ("HSBC", "HSBA.L", "GBp"),
            ("Unilever", "ULVR.L", "GBp"),
        ],
    },
    "Japan": {
        "label": "🇯🇵 Japan",
        "indexes": [
            ("Nikkei 225", "^N225", "JPY"),
            ("TOPIX", "^TPX", "JPY"),
        ],
        "stocks": [
            ("Toyota", "7203.T", "JPY"),
            ("Sony", "6758.T", "JPY"),
            ("SoftBank", "9984.T", "JPY"),
            ("Nintendo", "7974.T", "JPY"),
        ],
    },
    "Germany": {
        "label": "🇩🇪 Germany",
        "indexes": [
            ("DAX", "^GDAXI", "EUR"),
            ("MDAX", "^MDAXI", "EUR"),
        ],
        "stocks": [
            ("SAP", "SAP.DE", "EUR"),
            ("Siemens", "SIE.DE", "EUR"),
            ("Allianz", "ALV.DE", "EUR"),
            ("Mercedes-Benz", "MBG.DE", "EUR"),
        ],
    },
    "France": {
        "label": "🇫🇷 France",
        "indexes": [
            ("CAC 40", "^FCHI", "EUR"),
            ("SBF 120", "^SBF120", "EUR"),
        ],
        "stocks": [
            ("LVMH", "MC.PA", "EUR"),
            ("TotalEnergies", "TTE.PA", "EUR"),
            ("Schneider Electric", "SU.PA", "EUR"),
            ("Sanofi", "SAN.PA", "EUR"),
        ],
    },
    "Netherlands": {
        "label": "🇳🇱 Netherlands",
        "indexes": [
            ("AEX", "^AEX", "EUR"),
            ("AMX", "^AMX", "EUR"),
        ],
        "stocks": [
            ("ASML", "ASML.AS", "EUR"),
            ("ING Group", "INGA.AS", "EUR"),
            ("Adyen", "ADYEN.AS", "EUR"),
            ("Philips", "PHIA.AS", "EUR"),
        ],
    },
    "Spain": {
        "label": "🇪🇸 Spain",
        "indexes": [
            ("IBEX 35", "^IBEX", "EUR"),
            ("IBEX Medium Cap", "IBEXM.MC", "EUR"),
        ],
        "stocks": [
            ("Inditex", "ITX.MC", "EUR"),
            ("Banco Santander", "SAN.MC", "EUR"),
            ("Iberdrola", "IBE.MC", "EUR"),
            ("BBVA", "BBVA.MC", "EUR"),
        ],
    },
    "Italy": {
        "label": "🇮🇹 Italy",
        "indexes": [
            ("FTSE MIB", "FTSEMIB.MI", "EUR"),
            ("FTSE Italia All-Share", "ITLMS.MI", "EUR"),
        ],
        "stocks": [
            ("Enel", "ENEL.MI", "EUR"),
            ("Intesa Sanpaolo", "ISP.MI", "EUR"),
            ("Eni", "ENI.MI", "EUR"),
            ("UniCredit", "UCG.MI", "EUR"),
        ],
    },
    "Belgium": {
        "label": "🇧🇪 Belgium",
        "indexes": [
            ("BEL 20", "^BFX", "EUR"),
            ("BEL Mid", "BELM.BR", "EUR"),
        ],
        "stocks": [
            ("Anheuser-Busch InBev", "ABI.BR", "EUR"),
            ("KBC Group", "KBC.BR", "EUR"),
            ("UCB", "UCB.BR", "EUR"),
            ("Solvay", "SOLB.BR", "EUR"),
        ],
    },
    "Finland": {
        "label": "🇫🇮 Finland",
        "indexes": [
            ("OMX Helsinki 25", "^OMXH25", "EUR"),
            ("OMX Helsinki", "^OMXHPI", "EUR"),
        ],
        "stocks": [
            ("Nokia", "NOKIA.HE", "EUR"),
            ("Neste", "NESTE.HE", "EUR"),
            ("Kone", "KNEBV.HE", "EUR"),
            ("Sampo", "SAMPO.HE", "EUR"),
        ],
    },
    "Austria": {
        "label": "🇦🇹 Austria",
        "indexes": [
            ("ATX", "^ATX", "EUR"),
            ("ATX Prime", "ATXPRIME.VI", "EUR"),
        ],
        "stocks": [
            ("Erste Group", "EBS.VI", "EUR"),
            ("OMV", "OMV.VI", "EUR"),
            ("Verbund", "VER.VI", "EUR"),
            ("Andritz", "ANDR.VI", "EUR"),
        ],
    },
    "Portugal": {
        "label": "🇵🇹 Portugal",
        "indexes": [
            ("PSI", "PSI20.LS", "EUR"),
            ("PSI Geral", "PSING.LS", "EUR"),
        ],
        "stocks": [
            ("EDP", "EDP.LS", "EUR"),
            ("Galp Energia", "GALP.LS", "EUR"),
            ("Jeronimo Martins", "JMT.LS", "EUR"),
            ("Banco Comercial Portugues", "BCP.LS", "EUR"),
        ],
    },
    "Canada": {
        "label": "🇨🇦 Canada",
        "indexes": [
            ("TSX", "^GSPTSE", "CAD"),
            ("TSX Venture", "^SPCDNX", "CAD"),
        ],
        "stocks": [
            ("Shopify", "SHOP.TO", "CAD"),
            ("Royal Bank", "RY.TO", "CAD"),
            ("Enbridge", "ENB.TO", "CAD"),
            ("Brookfield", "BN.TO", "CAD"),
        ],
    },
    "Australia": {
        "label": "🇦🇺 Australia",
        "indexes": [
            ("ASX 200", "^AXJO", "AUD"),
            ("All Ordinaries", "^AORD", "AUD"),
        ],
        "stocks": [
            ("BHP", "BHP.AX", "AUD"),
            ("Commonwealth Bank", "CBA.AX", "AUD"),
            ("CSL", "CSL.AX", "AUD"),
            ("Wesfarmers", "WES.AX", "AUD"),
        ],
    },
    "Switzerland": {
        "label": "🇨🇭 Switzerland",
        "indexes": [
            ("Swiss Market Index", "^SSMI", "CHF"),
            ("Swiss Performance Index", "^SSHI", "CHF"),
        ],
        "stocks": [
            ("Nestle", "NESN.SW", "CHF"),
            ("Novartis", "NOVN.SW", "CHF"),
            ("Roche", "ROG.SW", "CHF"),
            ("UBS", "UBSG.SW", "CHF"),
        ],
    },
    "China": {
        "label": "🇨🇳 China",
        "indexes": [
            ("Shanghai Composite", "000001.SS", "CNY"),
            ("Shenzhen Component", "399001.SZ", "CNY"),
        ],
        "stocks": [
            ("Kweichow Moutai", "600519.SS", "CNY"),
            ("Ping An Insurance", "601318.SS", "CNY"),
            ("BYD", "002594.SZ", "CNY"),
            ("China Merchants Bank", "600036.SS", "CNY"),
        ],
    },
    "Singapore": {
        "label": "🇸🇬 Singapore",
        "indexes": [
            ("Straits Times Index", "^STI", "SGD"),
            ("FTSE ST Mid Cap", "FSTM.SI", "SGD"),
        ],
        "stocks": [
            ("DBS Group", "D05.SI", "SGD"),
            ("OCBC Bank", "O39.SI", "SGD"),
            ("UOB", "U11.SI", "SGD"),
            ("Singapore Airlines", "C6L.SI", "SGD"),
        ],
    },
    "United Arab Emirates": {
        "label": "🇦🇪 United Arab Emirates",
        "indexes": [
            ("DFM General Index", "DFMGI.AE", "AED"),
            ("ADX General Index", "ADI.AE", "AED"),
        ],
        "stocks": [
            ("Emaar Properties", "EMAAR.AE", "AED"),
            ("Dubai Islamic Bank", "DIB.AE", "AED"),
            ("Emirates NBD", "EMIRATESNBD.AE", "AED"),
            ("Aldar Properties", "ALDAR.AE", "AED"),
        ],
    },
}

GLOBAL_MARKET = {
    "indexes": [
        ("S&P 500", "^GSPC", "USD"),
        ("NASDAQ", "^IXIC", "USD"),
        ("Bitcoin", "BTC-USD", "USD"),
        ("Gold", "GC=F", "USD"),
    ],
    "stocks": [
        ("Apple", "AAPL", "USD"),
        ("Nvidia", "NVDA", "USD"),
        ("Reliance", "RELIANCE.NS", "INR"),
        ("Toyota", "7203.T", "JPY"),
    ],
}

QUICK_TOPIC_MARKETS = {
    "best_etfs": {
        "global": [
            ("SPDR S&P 500 ETF", "SPY", "USD"),
            ("Vanguard Total Stock Market ETF", "VTI", "USD"),
            ("Invesco QQQ Trust", "QQQ", "USD"),
            ("iShares MSCI ACWI ETF", "ACWI", "USD"),
        ],
        "countries": {
            "United States": [
                ("SPDR S&P 500 ETF", "SPY", "USD"),
                ("Vanguard Total Stock Market ETF", "VTI", "USD"),
                ("Invesco QQQ Trust", "QQQ", "USD"),
            ],
            "India": [
                ("Nippon India Nifty 50 Bees", "NIFTYBEES.NS", "INR"),
                ("SBI Nifty 50 ETF", "SETFNIF50.NS", "INR"),
                ("HDFC Nifty 50 ETF", "HDFCNIFTY.NS", "INR"),
            ],
            "United Kingdom": [
                ("iShares Core FTSE 100 ETF", "ISF.L", "GBp"),
                ("Vanguard FTSE 100 UCITS ETF", "VUKE.L", "GBp"),
            ],
            "Japan": [
                ("NEXT FUNDS Nikkei 225 ETF", "1321.T", "JPY"),
                ("iShares Core TOPIX ETF", "1475.T", "JPY"),
            ],
            "Germany": [
                ("iShares Core DAX ETF", "EXS1.DE", "EUR"),
                ("Xtrackers DAX UCITS ETF", "DBXD.DE", "EUR"),
            ],
            "Canada": [
                ("iShares S&P/TSX 60 ETF", "XIU.TO", "CAD"),
                ("Vanguard FTSE Canada ETF", "VCE.TO", "CAD"),
            ],
        },
    },
    "dividend": {
        "global": [
            ("Johnson & Johnson", "JNJ", "USD"),
            ("Coca-Cola", "KO", "USD"),
            ("Procter & Gamble", "PG", "USD"),
            ("Royal Bank of Canada", "RY.TO", "CAD"),
        ],
        "countries": {
            "United States": [("Coca-Cola", "KO", "USD"), ("Johnson & Johnson", "JNJ", "USD"), ("Procter & Gamble", "PG", "USD")],
            "India": [("HDFC Bank", "HDFCBANK.NS", "INR"), ("Infosys", "INFY.NS", "INR"), ("ITC", "ITC.NS", "INR")],
            "United Kingdom": [("Shell", "SHEL.L", "GBp"), ("HSBC", "HSBA.L", "GBp"), ("Unilever", "ULVR.L", "GBp")],
            "Japan": [("Toyota", "7203.T", "JPY"), ("Nintendo", "7974.T", "JPY"), ("Sony", "6758.T", "JPY")],
            "Germany": [("Allianz", "ALV.DE", "EUR"), ("Siemens", "SIE.DE", "EUR"), ("Mercedes-Benz", "MBG.DE", "EUR")],
            "Canada": [("Royal Bank", "RY.TO", "CAD"), ("Enbridge", "ENB.TO", "CAD"), ("Brookfield", "BN.TO", "CAD")],
        },
    },
    "ai": {
        "global": [
            ("Nvidia", "NVDA", "USD"),
            ("Microsoft", "MSFT", "USD"),
            ("Alphabet", "GOOGL", "USD"),
            ("Taiwan Semiconductor", "TSM", "USD"),
        ],
        "countries": {
            "United States": [("Nvidia", "NVDA", "USD"), ("Microsoft", "MSFT", "USD"), ("Alphabet", "GOOGL", "USD"), ("AMD", "AMD", "USD")],
            "India": [("TCS", "TCS.NS", "INR"), ("Infosys", "INFY.NS", "INR"), ("HCLTech", "HCLTECH.NS", "INR")],
            "United Kingdom": [("Sage Group", "SGE.L", "GBp"), ("Ocado", "OCDO.L", "GBp"), ("Darktrace", "DARK.L", "GBp")],
            "Japan": [("Sony", "6758.T", "JPY"), ("SoftBank", "9984.T", "JPY"), ("Tokyo Electron", "8035.T", "JPY")],
            "Germany": [("SAP", "SAP.DE", "EUR"), ("Siemens", "SIE.DE", "EUR"), ("Infineon", "IFX.DE", "EUR")],
            "Canada": [("Shopify", "SHOP.TO", "CAD"), ("Constellation Software", "CSU.TO", "CAD"), ("OpenText", "OTEX.TO", "CAD")],
        },
    },
    "undervalued": {
        "global": [
            ("Berkshire Hathaway", "BRK-B", "USD"),
            ("Toyota", "7203.T", "JPY"),
            ("Shell", "SHEL.L", "GBp"),
            ("HDFC Bank", "HDFCBANK.NS", "INR"),
        ],
        "countries": {
            "United States": [("Berkshire Hathaway", "BRK-B", "USD"), ("JPMorgan Chase", "JPM", "USD"), ("Intel", "INTC", "USD")],
            "India": [("HDFC Bank", "HDFCBANK.NS", "INR"), ("Reliance", "RELIANCE.NS", "INR"), ("Infosys", "INFY.NS", "INR")],
            "United Kingdom": [("Shell", "SHEL.L", "GBp"), ("HSBC", "HSBA.L", "GBp"), ("AstraZeneca", "AZN.L", "GBp")],
            "Japan": [("Toyota", "7203.T", "JPY"), ("Sony", "6758.T", "JPY"), ("Nintendo", "7974.T", "JPY")],
            "Germany": [("Mercedes-Benz", "MBG.DE", "EUR"), ("Allianz", "ALV.DE", "EUR"), ("Siemens", "SIE.DE", "EUR")],
            "Canada": [("Royal Bank", "RY.TO", "CAD"), ("Enbridge", "ENB.TO", "CAD"), ("Brookfield", "BN.TO", "CAD")],
        },
    },
}


COUNTRY_ETFS = {
    "United States": [
        ("SPDR S&P 500 ETF", "SPY", "USD"),
        ("Vanguard Total Stock Market ETF", "VTI", "USD"),
        ("Invesco QQQ Trust", "QQQ", "USD"),
    ],
    "India": [
        ("Nippon India Nifty 50 Bees", "NIFTYBEES.NS", "INR"),
        ("SBI Nifty 50 ETF", "SETFNIF50.NS", "INR"),
        ("HDFC Nifty 50 ETF", "HDFCNIFTY.NS", "INR"),
    ],
    "United Kingdom": [
        ("iShares MSCI United Kingdom ETF", "EWU", "USD"),
        ("iShares Core FTSE 100 ETF", "ISF.L", "GBp"),
        ("Vanguard FTSE 100 UCITS ETF", "VUKE.L", "GBp"),
    ],
    "Japan": [
        ("iShares MSCI Japan ETF", "EWJ", "USD"),
        ("NEXT FUNDS Nikkei 225 ETF", "1321.T", "JPY"),
        ("iShares Core TOPIX ETF", "1475.T", "JPY"),
    ],
    "Germany": [
        ("iShares MSCI Germany ETF", "EWG", "USD"),
        ("iShares Core DAX ETF", "EXS1.DE", "EUR"),
        ("Xtrackers DAX UCITS ETF", "DBXD.DE", "EUR"),
    ],
    "France": [
        ("iShares MSCI France ETF", "EWQ", "USD"),
        ("Lyxor CAC 40 UCITS ETF", "CAC.PA", "EUR"),
    ],
    "Netherlands": [
        ("iShares MSCI Netherlands ETF", "EWN", "USD"),
        ("iShares AEX UCITS ETF", "IAEX.AS", "EUR"),
    ],
    "Spain": [
        ("iShares MSCI Spain ETF", "EWP", "USD"),
        ("Lyxor IBEX 35 UCITS ETF", "LYXIB.MC", "EUR"),
    ],
    "Italy": [
        ("iShares MSCI Italy ETF", "EWI", "USD"),
        ("iShares FTSE MIB UCITS ETF", "CSMIB.MI", "EUR"),
    ],
    "Belgium": [
        ("iShares MSCI Belgium ETF", "EWK", "USD"),
    ],
    "Finland": [
        ("iShares MSCI Finland ETF", "EFNL", "USD"),
    ],
    "Austria": [
        ("iShares MSCI Austria ETF", "EWO", "USD"),
    ],
    "Portugal": [
        ("Global X MSCI Portugal ETF", "PGAL", "USD"),
    ],
    "Canada": [
        ("iShares MSCI Canada ETF", "EWC", "USD"),
        ("iShares S&P/TSX 60 ETF", "XIU.TO", "CAD"),
        ("Vanguard FTSE Canada ETF", "VCE.TO", "CAD"),
    ],
    "Australia": [
        ("iShares MSCI Australia ETF", "EWA", "USD"),
    ],
    "Switzerland": [
        ("iShares MSCI Switzerland ETF", "EWL", "USD"),
    ],
    "China": [
        ("iShares China Large-Cap ETF", "FXI", "USD"),
        ("iShares MSCI China ETF", "MCHI", "USD"),
    ],
    "Singapore": [
        ("iShares MSCI Singapore ETF", "EWS", "USD"),
    ],
    "United Arab Emirates": [
        ("iShares MSCI UAE ETF", "UAE", "USD"),
    ],
}


TOPIC_FALLBACK_MARKETS = {
    "dividend": {
        "France": [
            ("TotalEnergies", "TTE.PA", "EUR"),
            ("Sanofi", "SAN.PA", "EUR"),
            ("BNP Paribas", "BNP.PA", "EUR"),
            ("Orange", "ORA.PA", "EUR"),
        ],
        "Netherlands": [
            ("ING Group", "INGA.AS", "EUR"),
            ("NN Group", "NN.AS", "EUR"),
            ("ASR Nederland", "ASRNL.AS", "EUR"),
            ("Ahold Delhaize", "AD.AS", "EUR"),
        ],
        "Spain": [
            ("Iberdrola", "IBE.MC", "EUR"),
            ("Banco Santander", "SAN.MC", "EUR"),
            ("BBVA", "BBVA.MC", "EUR"),
            ("Endesa", "ELE.MC", "EUR"),
        ],
        "Italy": [
            ("Enel", "ENEL.MI", "EUR"),
            ("Intesa Sanpaolo", "ISP.MI", "EUR"),
            ("Eni", "ENI.MI", "EUR"),
            ("UniCredit", "UCG.MI", "EUR"),
        ],
        "Belgium": [
            ("KBC Group", "KBC.BR", "EUR"),
            ("Ageas", "AGS.BR", "EUR"),
            ("Proximus", "PROX.BR", "EUR"),
            ("Anheuser-Busch InBev", "ABI.BR", "EUR"),
        ],
        "Finland": [
            ("Sampo", "SAMPO.HE", "EUR"),
            ("Fortum", "FORTUM.HE", "EUR"),
            ("UPM-Kymmene", "UPM.HE", "EUR"),
            ("Nokia", "NOKIA.HE", "EUR"),
        ],
        "Austria": [
            ("Erste Group", "EBS.VI", "EUR"),
            ("OMV", "OMV.VI", "EUR"),
            ("Verbund", "VER.VI", "EUR"),
            ("Vienna Insurance", "VIG.VI", "EUR"),
        ],
        "Portugal": [
            ("EDP", "EDP.LS", "EUR"),
            ("Galp Energia", "GALP.LS", "EUR"),
            ("Jeronimo Martins", "JMT.LS", "EUR"),
            ("Banco Comercial Portugues", "BCP.LS", "EUR"),
        ],
        "Australia": [
            ("Commonwealth Bank", "CBA.AX", "AUD"),
            ("BHP", "BHP.AX", "AUD"),
            ("Wesfarmers", "WES.AX", "AUD"),
            ("Telstra", "TLS.AX", "AUD"),
        ],
        "Switzerland": [
            ("Nestle", "NESN.SW", "CHF"),
            ("Novartis", "NOVN.SW", "CHF"),
            ("Roche", "ROG.SW", "CHF"),
            ("Zurich Insurance", "ZURN.SW", "CHF"),
        ],
        "China": [
            ("China Merchants Bank", "600036.SS", "CNY"),
            ("Ping An Insurance", "601318.SS", "CNY"),
            ("Industrial and Commercial Bank of China", "601398.SS", "CNY"),
            ("China Yangtze Power", "600900.SS", "CNY"),
        ],
        "Singapore": [
            ("DBS Group", "D05.SI", "SGD"),
            ("OCBC Bank", "O39.SI", "SGD"),
            ("UOB", "U11.SI", "SGD"),
            ("Singapore Telecommunications", "Z74.SI", "SGD"),
        ],
        "United Arab Emirates": [
            ("Emirates NBD", "EMIRATESNBD.AE", "AED"),
            ("Dubai Islamic Bank", "DIB.AE", "AED"),
            ("Emaar Properties", "EMAAR.AE", "AED"),
            ("DEWA", "DEWA.AE", "AED"),
        ],
    },
    "ai": {
        "France": [
            ("Dassault Systemes", "DSY.PA", "EUR"),
            ("Schneider Electric", "SU.PA", "EUR"),
            ("Capgemini", "CAP.PA", "EUR"),
            ("STMicroelectronics", "STMPA.PA", "EUR"),
        ],
        "Netherlands": [
            ("ASML", "ASML.AS", "EUR"),
            ("ASM International", "ASM.AS", "EUR"),
            ("BE Semiconductor", "BESI.AS", "EUR"),
            ("Adyen", "ADYEN.AS", "EUR"),
        ],
        "Spain": [
            ("Amadeus IT", "AMS.MC", "EUR"),
            ("Indra Sistemas", "IDR.MC", "EUR"),
            ("Telefonica", "TEF.MC", "EUR"),
            ("Cellnex Telecom", "CLNX.MC", "EUR"),
        ],
        "Italy": [
            ("STMicroelectronics", "STM.MI", "EUR"),
            ("Leonardo", "LDO.MI", "EUR"),
            ("Telecom Italia", "TIT.MI", "EUR"),
            ("Prysmian", "PRY.MI", "EUR"),
        ],
        "Belgium": [
            ("Melexis", "MELE.BR", "EUR"),
            ("Barco", "BAR.BR", "EUR"),
            ("UCB", "UCB.BR", "EUR"),
            ("Solvay", "SOLB.BR", "EUR"),
        ],
        "Finland": [
            ("Nokia", "NOKIA.HE", "EUR"),
            ("Qt Group", "QTCOM.HE", "EUR"),
            ("Tietoevry", "TIETO.HE", "EUR"),
            ("Kone", "KNEBV.HE", "EUR"),
        ],
        "Austria": [
            ("ams-OSRAM", "AMS.VI", "EUR"),
            ("Andritz", "ANDR.VI", "EUR"),
            ("AT&S", "ATS.VI", "EUR"),
            ("Kontron", "KTN.VI", "EUR"),
        ],
        "Portugal": [
            ("EDP Renovaveis", "EDPR.LS", "EUR"),
            ("Nos", "NOS.LS", "EUR"),
            ("Jeronimo Martins", "JMT.LS", "EUR"),
            ("EDP", "EDP.LS", "EUR"),
        ],
        "Australia": [
            ("WiseTech Global", "WTC.AX", "AUD"),
            ("Xero", "XRO.AX", "AUD"),
            ("NextDC", "NXT.AX", "AUD"),
            ("Technology One", "TNE.AX", "AUD"),
        ],
        "Switzerland": [
            ("Logitech", "LOGN.SW", "CHF"),
            ("VAT Group", "VACN.SW", "CHF"),
            ("Kudelski", "KUD.SW", "CHF"),
            ("U-blox", "UBXN.SW", "CHF"),
        ],
        "China": [
            ("BYD", "002594.SZ", "CNY"),
            ("Foxconn Industrial Internet", "601138.SS", "CNY"),
            ("iFlytek", "002230.SZ", "CNY"),
            ("Hikvision", "002415.SZ", "CNY"),
        ],
        "Singapore": [
            ("Sea Limited", "SE", "USD"),
            ("Venture Corp", "V03.SI", "SGD"),
            ("ST Engineering", "S63.SI", "SGD"),
            ("AEM Holdings", "AWX.SI", "SGD"),
        ],
        "United Arab Emirates": [
            ("Presight AI", "PRESIGHT.AE", "AED"),
            ("e&", "EAND.AE", "AED"),
            ("Salik", "SALIK.AE", "AED"),
            ("Multiply Group", "MULTIPLY.AE", "AED"),
        ],
    },
    "undervalued": {
        "France": [
            ("TotalEnergies", "TTE.PA", "EUR"),
            ("BNP Paribas", "BNP.PA", "EUR"),
            ("Renault", "RNO.PA", "EUR"),
            ("Orange", "ORA.PA", "EUR"),
        ],
        "Netherlands": [
            ("ING Group", "INGA.AS", "EUR"),
            ("Philips", "PHIA.AS", "EUR"),
            ("Akzo Nobel", "AKZA.AS", "EUR"),
            ("Ahold Delhaize", "AD.AS", "EUR"),
        ],
        "Spain": [
            ("Banco Santander", "SAN.MC", "EUR"),
            ("BBVA", "BBVA.MC", "EUR"),
            ("Telefonica", "TEF.MC", "EUR"),
            ("Repsol", "REP.MC", "EUR"),
        ],
        "Italy": [
            ("UniCredit", "UCG.MI", "EUR"),
            ("Intesa Sanpaolo", "ISP.MI", "EUR"),
            ("Eni", "ENI.MI", "EUR"),
            ("Stellantis", "STLAM.MI", "EUR"),
        ],
        "Belgium": [
            ("Anheuser-Busch InBev", "ABI.BR", "EUR"),
            ("Solvay", "SOLB.BR", "EUR"),
            ("Proximus", "PROX.BR", "EUR"),
            ("Ageas", "AGS.BR", "EUR"),
        ],
        "Finland": [
            ("Nokia", "NOKIA.HE", "EUR"),
            ("Neste", "NESTE.HE", "EUR"),
            ("UPM-Kymmene", "UPM.HE", "EUR"),
            ("Fortum", "FORTUM.HE", "EUR"),
        ],
        "Austria": [
            ("OMV", "OMV.VI", "EUR"),
            ("Erste Group", "EBS.VI", "EUR"),
            ("Voestalpine", "VOE.VI", "EUR"),
            ("Raiffeisen Bank", "RBI.VI", "EUR"),
        ],
        "Portugal": [
            ("Banco Comercial Portugues", "BCP.LS", "EUR"),
            ("Galp Energia", "GALP.LS", "EUR"),
            ("EDP", "EDP.LS", "EUR"),
            ("Semapa", "SEM.LS", "EUR"),
        ],
        "Australia": [
            ("BHP", "BHP.AX", "AUD"),
            ("Rio Tinto", "RIO.AX", "AUD"),
            ("Woodside Energy", "WDS.AX", "AUD"),
            ("ANZ Group", "ANZ.AX", "AUD"),
        ],
        "Switzerland": [
            ("UBS", "UBSG.SW", "CHF"),
            ("Roche", "ROG.SW", "CHF"),
            ("Holcim", "HOLN.SW", "CHF"),
            ("Swiss Re", "SREN.SW", "CHF"),
        ],
        "China": [
            ("Ping An Insurance", "601318.SS", "CNY"),
            ("China Merchants Bank", "600036.SS", "CNY"),
            ("SAIC Motor", "600104.SS", "CNY"),
            ("China Petroleum", "600028.SS", "CNY"),
        ],
        "Singapore": [
            ("DBS Group", "D05.SI", "SGD"),
            ("OCBC Bank", "O39.SI", "SGD"),
            ("UOB", "U11.SI", "SGD"),
            ("Wilmar International", "F34.SI", "SGD"),
        ],
        "United Arab Emirates": [
            ("Emaar Properties", "EMAAR.AE", "AED"),
            ("Aldar Properties", "ALDAR.AE", "AED"),
            ("ADNOC Gas", "ADNOCGAS.AE", "AED"),
            ("Emirates NBD", "EMIRATESNBD.AE", "AED"),
        ],
    },
}



def _currency_prefix(currency: str) -> str:
    return {
        "USD": "$",
        "EUR": "€",
        "INR": "₹",
        "JPY": "¥",
        "CAD": "C$",
        "GBp": "£",
        "AUD": "A$",
        "CHF": "CHF ",
        "CNY": "¥",
        "SGD": "S$",
        "AED": "د.إ",
    }.get(currency, "")


def _format_live_price(price, currency: str) -> str:
    if price is None:
        return "Unavailable"

    try:
        price = float(price)
    except (TypeError, ValueError):
        return "Unavailable"

    if price != price:
        return "Unavailable"

    decimals = 0 if currency in {"", "JPY", "GBp"} else 2
    if currency == "GBp":
        price = price / 100
        decimals = 2
    return f"{_currency_prefix(currency)}{price:,.{decimals}f}"


def _format_live_change(price, previous_close) -> str | None:
    if price is None or previous_close is None:
        return None

    try:
        price = float(price)
        previous_close = float(previous_close)
    except (TypeError, ValueError):
        return None

    if price != price or previous_close != previous_close:
        return None

    if previous_close <= 0:
        return None

    pct = ((price - previous_close) / previous_close) * 100
    return f"{pct:+.2f}%"


def _live_change_score(symbol: str) -> float | None:
    try:
        live = load_live_price(symbol)
        price = float(live.get("price"))
        previous_close = float(live.get("previous_close"))
    except (TypeError, ValueError, Exception):
        return None

    if price != price or previous_close != previous_close or previous_close <= 0:
        return None

    return ((price - previous_close) / previous_close) * 100


def rank_available_stocks(
    candidates: list[tuple[str, str, str]],
    limit: int = 5,
) -> list[tuple[str, str, str]]:
    ranked = []
    seen = set()
    for stock in candidates:
        symbol = stock[1]
        if symbol in seen:
            continue
        seen.add(symbol)

        score = _live_change_score(symbol)
        if score is None:
            continue
        ranked.append((score, stock))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [stock for _score, stock in ranked[:limit]]


def get_live_market_quote(symbol: str, currency: str) -> tuple[str, str]:
    try:
        live = load_live_price(symbol)
    except Exception:
        return t("common.unavailable"), t("homepage.not_available")

    price = live.get("price")
    previous_close = live.get("previous_close")
    return (
        _format_live_price(price, currency).replace("Unavailable", t("common.unavailable")),
        _format_live_change(price, previous_close) or t("homepage.not_available"),
    )


def get_homepage_market_data(selected_countries: list[str]) -> tuple[list, list]:
    if not selected_countries:
        return GLOBAL_MARKET["indexes"], rank_available_stocks(GLOBAL_MARKET["stocks"])

    indexes = []
    stocks = []
    for country in selected_countries:
        market = COUNTRY_MARKETS.get(country)
        if market:
            indexes.extend(market["indexes"])
            stocks.extend(market["stocks"])

    return indexes[:4], rank_available_stocks(stocks)


def get_quick_topic_stocks(topic: str, selected_countries: list[str]) -> list[tuple[str, str, str]]:
    topic_data = QUICK_TOPIC_MARKETS.get(topic)
    if not topic_data:
        return get_homepage_market_data(selected_countries)[1]

    if not selected_countries:
        return rank_available_stocks(topic_data["global"])

    stocks = []
    seen = set()
    for country in selected_countries:
        country_stocks = topic_data["countries"].get(country, [])
        if not country_stocks:
            if topic == "best_etfs":
                country_stocks = COUNTRY_ETFS.get(country, [])
            else:
                country_stocks = TOPIC_FALLBACK_MARKETS.get(topic, {}).get(country, [])
                if not country_stocks:
                    country_stocks = COUNTRY_MARKETS.get(country, {}).get("stocks", [])

        for stock in country_stocks:
            if stock[1] in seen:
                continue
            seen.add(stock[1])
            stocks.append(stock)
    return rank_available_stocks(stocks)


def get_ai_picks(selected_countries: list[str]) -> list[tuple[str, str, str]]:
    picks = get_quick_topic_stocks("ai", selected_countries)
    reason_keys = [
        "homepage.ai_pick_momentum",
        "homepage.ai_pick_growth",
        "homepage.ai_pick_expansion",
    ]
    return [
        (symbol, company_name, t(reason_keys[index % len(reason_keys)]))
        for index, (company_name, symbol, _currency) in enumerate(picks[:3])
    ]


def _countries_from_query(country_options: list[str]) -> list[str]:
    countries_value = _query_param(st.query_params, "countries")
    if st.session_state.get("countries_url_value") == countries_value:
        return st.session_state.selected_countries

    selected = []
    if countries_value:
        selected = [
            country
            for country in countries_value.split(",")
            if country in country_options
        ][:5]

    st.session_state.selected_countries = selected
    st.session_state.countries_url_value = countries_value
    return selected


def _sync_countries_to_url(selected_countries: list[str]) -> None:
    countries_value = ",".join(selected_countries[:5])
    _set_query_param("countries", countries_value or None)
    st.session_state.countries_url_value = countries_value or None


def stock_url(ticker: str, company_name: str) -> str:
    params = {}
    for key in ("lang", "q", "countries"):
        value = _query_param(st.query_params, key)
        if value:
            params[key] = value
    topic = _query_param(st.query_params, "topic")
    if topic and topic != "trending":
        params["topic"] = topic
    params["stock"] = ticker
    params["company"] = company_name
    return f"?{urlencode(params)}"



def render_homepage() -> None:
    if st.session_state.selected_ticker or st.session_state.search_results:
        return

    st.markdown("""
    <style>
    .stock-card {
        display: block;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        color: var(--text) !important;
        text-decoration: none !important;
        font-size: 0.9rem;
        line-height: 1.45;
    }
    .stock-card:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
    }
    .stock-card b {
        color: inherit;
    }
    .stock-card .positive {
        color: var(--green);
        font-family: var(--mono);
    }
    .stock-card .negative {
        color: var(--red);
        font-family: var(--mono);
    }
    .stock-card .neutral {
        color: var(--muted);
        font-family: var(--mono);
    }
    .ai-pick-link {
        display: block;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        color: var(--text) !important;
        text-decoration: none !important;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .ai-pick-link:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"### 🚀 {t('homepage.quick_explore')}")

    country_options = list(COUNTRY_MARKETS.keys())
    _countries_from_query(country_options)
    selected_countries = st.multiselect(
        t("homepage.country"),
        country_options,
        format_func=lambda country: COUNTRY_MARKETS[country]["label"],
        key="selected_countries",
        placeholder=t("homepage.country_placeholder"),
        max_selections=5,
    )
    _sync_countries_to_url(selected_countries)

    q1, q2, q3, q4 = st.columns(4)

    with q1:
        if st.button(t("homepage.best_etfs"), use_container_width=True):
            set_quick_topic("best_etfs")

    with q2:
        if st.button(t("homepage.dividend_stocks"), use_container_width=True):
            set_quick_topic("dividend")

    with q3:
        if st.button(t("homepage.ai_stocks"), use_container_width=True):
            set_quick_topic("ai")

    with q4:
        if st.button(t("homepage.undervalued_stocks"), use_container_width=True):
            set_quick_topic("undervalued")

    market_indexes, trending_stocks = get_homepage_market_data(selected_countries)
    quick_topic = st.session_state.get("quick_topic", "trending")
    display_stocks = (
        trending_stocks
        if quick_topic == "trending"
        else get_quick_topic_stocks(quick_topic, selected_countries)
    )

    # Market Snapshot
    snapshot_title = (
        f"### 📊 {t('homepage.global_market_snapshot')}"
        if not selected_countries
        else f"### 📊 {t('homepage.selected_country_markets')}"
    )
    st.markdown(snapshot_title)

    snapshot_cols = st.columns(4)
    for i, (label, symbol, market_currency) in enumerate(market_indexes):
        value, delta = get_live_market_quote(symbol, market_currency)
        with snapshot_cols[i % 4]:
            st.metric(label, value, delta)


    # Main content
    left, right = st.columns([2, 1])

    with left:
        if quick_topic == "trending":
            section_title = (
                f"### 🔥 {t('homepage.global_trending_stocks')}"
                if not selected_countries
                else f"### 🔥 {t('homepage.trending_stocks_by_country')}"
            )
        else:
            title_by_topic = {
                "best_etfs": t("homepage.best_etfs"),
                "dividend": t("homepage.dividend_stocks"),
                "ai": t("homepage.ai_stocks"),
                "undervalued": t("homepage.undervalued_stocks"),
            }
            section_title = f"### 🔎 {title_by_topic.get(quick_topic, t('homepage.global_trending_stocks'))}"
        st.markdown(section_title)

        visible_count = 0
        for stock, symbol, stock_currency in display_stocks:
            price, change = get_live_market_quote(symbol, stock_currency)
            if price == t("common.unavailable"):
                continue

            change_class = "positive" if change.startswith("+") else "negative" if change.startswith("-") else "neutral"
            st.markdown(f"""
            <a class="stock-card" href="{stock_url(symbol, stock)}">
                <b>{escape(stock)}</b> <span style="color:#64748b;font-family:var(--mono);font-size:0.78rem">{escape(symbol)}</span><br>
                {t("homepage.price")}: {price}<br>
                {t("homepage.change")}: <span class="{change_class}">{change}</span>
            </a>
            """, unsafe_allow_html=True)
            visible_count += 1
            if visible_count >= 5:
                break

    with right:
        st.markdown(f"### 🤖 {t('homepage.ai_picks_today')}")

        ai_picks = get_ai_picks(selected_countries)

        for ticker, company_name, reason in ai_picks:
            st.markdown(
                f'<a class="ai-pick-link" href="{stock_url(ticker, company_name)}">'
                f'{ticker} → {reason}</a>',
                unsafe_allow_html=True,
            )


    # Educational section
    st.markdown(f"### 📚 {t('homepage.learn_before_invest')}")

    e1, e2, e3 = st.columns(3)

    with e1:
        with st.expander(t("homepage.analyze_stock_title")):
            st.markdown(t("homepage.analyze_stock_body"))

    with e2:
        with st.expander(t("homepage.etf_basics_title")):
            st.markdown(t("homepage.etf_basics_body"))

    with e3:
        with st.expander(t("homepage.risk_management_title")):
            st.markdown(t("homepage.risk_management_body"))
