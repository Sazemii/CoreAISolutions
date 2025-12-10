# CoreAISolutions - Odoo Custom Addons

Custom Odoo modules developed by CoreAI Solutions.

## Modules

### CAI POS (cai_pos)
BIR-compliant POS module for Philippines taxation requirements.

**Features:**
- BIR-compliant receipt format
- Senior Citizen (SC) and PWD discount support with VAT-exempt calculations
- X-Reading and Z-Reading reports
- eSales monthly report generation (CSV/Excel)
- Void transaction management with audit trail
- Government and promotional discount types

**Version:** 18.0.1.0.0  
**License:** LGPL-3  
**Dependencies:** `point_of_sale`, `account`, `mail`

## Installation

### For Odoo.sh
1. Link this repository to your Odoo.sh project
2. The modules will be automatically detected

### For Self-Hosted Odoo
1. Clone this repository to your addons path
2. Update the apps list in Odoo
3. Install the desired module(s)

## Configuration

After installing `cai_pos`:
1. Go to **Point of Sale → BIR Compliance → BIR Configurations**
2. Create a new BIR Configuration with your business details:
   - TIN (Tax Identification Number)
   - BIR Permit Number
   - MIN (Machine Identification Number)
   - Accreditation Number
3. Link the BIR Configuration to your POS in **Point of Sale → Configuration → Point of Sale**

## Support

For support and inquiries, please contact CoreAI Solutions.

---
*Developed for Odoo 18.0*

