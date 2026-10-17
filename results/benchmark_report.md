# Benchmark results

Run 2026-10-18 · model `qwen2.5-coder-7b-instruct-q4_k_m` · 40 questions · temperature 0 · one retry after an error.

| | LLM + raw SQL | LLM + governed metrics |
|---|---|---|
| **Correct answers** | **60%** (24/40) | **70%** (28/40) |
| Revenue funnel (16) | 38% | 75% |
| Customer experience (15) | 60% | 67% |
| Workforce (4) | 100% | 25% |
| Not answerable (should refuse) (5) | 100% | 100% |
| Questions with a definition trap (19) | 58% | 68% |
| Invented an answer to an unanswerable question | 0 | 0 |
| Failed to produce a valid query after one retry | 2 | 5 |

## Outcome by question

| # | Question | Raw SQL | Governed | Gold |
|---|---|---|---|---|
| q01 | How many unique leads did we receive in March 2025? | ✅ 6936 | ✅ 6936 | 6936 |
| q02 | What was our overall contact rate for leads created between January and June 2025? | ❌ 0.6833 (wrong value) | ✅ 0.662644 | 0.662644 |
| q03 | What was the lead conversion rate for leads created in Q2 2025? | ❌ 0.0871 (wrong value) | ❌ - (execution error) | 0.0891316 |
| q04 | Which lead vendor had the highest conversion rate from January to June 2025? | ❌ - (execution error) | ✅ Harbor Referral Network | Harbor Referral Network |
| q05 | What was the lead cost per sale for Clickstream Media from 15 March to 30 June 2025? | ❌ 812.806 (wrong value) | ❌ - (execution error) | 1263.95 |
| q06 | Which paid lead vendor had the highest lead cost per sale from 15 March to 30 June 2025? | ❌ refused (false refusal) | ❌ - (execution error) | Clickstream Media |
| q07 | What was the average speed to lead, in business minutes, for leads created in April 2025? | ✅ 16.1271 | ✅ 16.1021 | 16.1021 |
| q08 | What share of sales never became an active subscription, across January to June 2025? | ❌ 0.911904 (wrong value) | ✅ 0.105341 | 0.105341 |
| q09 | What was the booked annual value of sales from leads created in May 2025? | ✅ 546240 | ✅ 546240 | 546240 |
| q10 | What was the activation rate of sales for leads created in February 2025? | ❌ 0.106367 (wrong value) | ✅ 0.910273 | 0.910273 |
| q11 | What share of all non-test lead records were duplicates, January to June 2025? | ❌ 0.149581 (wrong value) | ✅ 0.134388 | 0.134388 |
| q12 | What was the qualification rate (qualified leads out of contacted leads) for January to June 2025? | ✅ 0.457867 | ✅ 0.457867 | 0.457867 |
| q13 | Which site had the slower average speed to lead in June 2025? | ❌ Tampa (wrong value) | ✅ Phoenix | Phoenix |
| q14 | What was the conversion rate for leads first dialed within 5 business minutes, January to June 2025? | ❌ 0.1086 (wrong value) | ❌ - (no answer) | 0.123889 |
| q15 | How much did we spend on lead vendors in Q1 2025? | ✅ 710886 | ✅ 710886 | 710886 |
| q16 | In which month was the lead conversion rate lowest (by lead creation month)? Answer as YYYY-MM. | ✅ 2025-06-01 00:00:00 | ✅ 2025-06-01 00:00:00 | 2025-06 |
| q17 | How many customer contacts did we have in March 2025, across all channels? | ✅ 3705 | ✅ 3705 | 3705 |
| q18 | What was the average handle time, in seconds, for agent-handled contacts in April 2025? | ✅ 618.36 | ✅ 618.36 | 618.36 |
| q19 | What was our first-contact resolution rate from January to June 2025? | ❌ 0.8285 (wrong value) | ❌ 0.828006 (wrong value) | 0.825307 |
| q20 | What was the bot's containment rate from January to June 2025? | ✅ 0.8525 | ✅ 0.852481 | 0.852499 |
| q21 | What share of bot sessions actually resolved the customer's issue, January to June 2025? | ❌ 0.726395 (wrong value) | ✅ 0.604635 | 0.60455 |
| q22 | Which contact driver (most detailed level) has the lowest bot true resolution rate? | ❌ refused (false refusal) | ✅ Cancel service | Cancel service |
| q23 | What was the repeat contact rate from January to June 2025? | ❌ refused (false refusal) | ❌ 0.196246 (wrong value) | 0.203179 |
| q24 | What was the total cost to serve customer contacts in May 2025? | ✅ 9422.75 | ✅ 9422.75 | 9422.75 |
| q25 | What was the cost per contact in June 2025? | ✅ 2.53442 | ✅ 2.53442 | 2.53442 |
| q26 | What share of contacting customers cancelled within 30 days of the contact, January to June 2025? | ✅ 0.0789716 | ❌ - (execution error) | 0.0803687 |
| q27 | Which top-level contact driver category had the most contacts from January to June 2025? | ❌ - (execution error) | ✅ Billing | Billing |
| q28 | What was the resolution rate for Billing contacts (all channels), January to June 2025? | ❌ 0.515705 (wrong value) | ❌ - (no answer) | 0.708198 |
| q29 | How many bot sessions did we have in Q2 2025? | ✅ 5482 | ✅ 5482 | 5482 |
| q30 | Which handling path (agent, bot only, bot then agent, abandoned) had the highest cost per contact? | ✅ bot then agent | ✅ bot then agent | bot then agent |
| q31 | How many agent-handled contacts ended in the Tech Support queue in March 2025? | ✅ 502 | ❌ 603 (wrong value) | 502 |
| q32 | What was schedule adherence for Phoenix agents in Q1 2025? | ✅ 0.880574 | ❌ - (execution error) | 0.880574 |
| q33 | What was total agent labor cost from January to June 2025? | ✅ 4454328 | ✅ 4454328 | 4454328 |
| q34 | How many sales per paid hour did tier 1 agents make from January to June 2025? | ✅ 0.0230896 | ❌ - (no answer) | 0.0230896 |
| q35 | Which site had the lower schedule adherence from January to June 2025? | ✅ Phoenix | ❌ Tampa (wrong value) | Phoenix |
| q36 | What was our Net Promoter Score in March 2025? | ✅ refused | ✅ refused | refuse |
| q37 | What is the average order value of equipment purchases in Q2 2025? | ✅ refused | ✅ refused | refuse |
| q38 | How many website visitors did we have in May 2025? | ✅ refused | ✅ refused | refuse |
| q39 | Which site has the higher employee satisfaction score? | ✅ refused | ✅ refused | refuse |
| q40 | What was the conversion rate of our Facebook campaign in Q1 2025? | ✅ refused | ✅ empty result | refuse |

## Where the raw-SQL agent went wrong

**q02. What was our overall contact rate for leads created between January and June 2025?** — wrong value. Trap: Contact rate is per lead; computing it from dial attempts gives a much lower number. Answer 0.6833, gold 0.662644.

```sql
SELECT contact_rate FROM marts.mart_monthly_kpis WHERE report_month BETWEEN '2025-01-01' AND '2025-06-30'
```

**q03. What was the lead conversion rate for leads created in Q2 2025?** — wrong value. Answer 0.0871, gold 0.0891316.

```sql
SELECT conversion_rate FROM marts.mart_monthly_kpis WHERE report_month BETWEEN '2025-04-01' AND '2025-06-30'
```

**q04. Which lead vendor had the highest conversion rate from January to June 2025?** — execution error. 

```sql
SELECT vendor_name FROM marts.fct_lead_journey WHERE created_date BETWEEN '2025-01-01' AND '2025-06-30' GROUP BY vendor_name ORDER BY CAST(sold_count AS FLOAT) / contacted_count DESC LIMIT 1
```

**q05. What was the lead cost per sale for Clickstream Media from 15 March to 30 June 2025?** — wrong value. Trap: Spend and sales live in different tables; both must be limited to the same window. Answer 812.806, gold 1263.95.

```sql
SELECT SUM(fct_lead_journey.won_amount_usd) / COUNT(fct_lead_journey.lead_id) AS lead_cost_per_sale FROM marts.fct_lead_journey JOIN marts.dim_lead_vendor ON fct_lead_journey.vendor_name = marts.dim_lead_vendor.vendor_name WHERE marts.dim_lead_vendor.vendor_name = 'Clickstream Media' AND fct_lead_journey.sold_at_utc BETWEEN '2025-03-15 00:00:00' AND '2025-06-30 23:59:59'
```

**q06. Which paid lead vendor had the highest lead cost per sale from 15 March to 30 June 2025?** — false refusal. Trap: The cheapest vendor per lead is the most expensive per sale. 

```sql
SELECT vendor_name FROM marts.fct_lead_journey WHERE sold_at_utc BETWEEN '2025-03-15 00:00:00' AND '2025-06-30 23:59:59' GROUP BY vendor_name ORDER BY SUM(cost_to_serve_usd) / SUM(sales) DESC LIMIT 1
```

**q08. What share of sales never became an active subscription, across January to June 2025?** — wrong value. Trap: The denominator is sales, not leads. Answer 0.911904, gold 0.105341.

```sql
SELECT CAST(SUM(CASE WHEN fct_lead_journey.is_activated = false THEN 1 ELSE 0 END) AS REAL) / COUNT(fct_lead_journey.lead_id) AS share_of_sales_never_became_active FROM marts.fct_lead_journey WHERE fct_lead_journey.created_date BETWEEN '2025-01-01' AND '2025-06-30'
```

**q10. What was the activation rate of sales for leads created in February 2025?** — wrong value. Trap: Activation rate is activations over sales, not over leads. Answer 0.106367, gold 0.910273.

```sql
SELECT AVG(CAST(is_activated AS DOUBLE)) AS activation_rate FROM marts.fct_lead_journey WHERE EXTRACT(YEAR FROM created_date) = 2025 AND EXTRACT(MONTH FROM created_date) = 2
```

**q11. What share of all non-test lead records were duplicates, January to June 2025?** — wrong value. Trap: Duplicates are a count on the unique lead, so the denominator is duplicates plus unique leads. Answer 0.149581, gold 0.134388.

```sql
SELECT CAST(SUM(CASE WHEN duplicate_lead_count > 0 THEN 1 ELSE 0 END) AS REAL) / COUNT(*) AS duplicate_share FROM marts.fct_lead_journey WHERE created_date BETWEEN '2025-01-01' AND '2025-06-30'
```

**q13. Which site had the slower average speed to lead in June 2025?** — wrong value. Answer Tampa, gold Phoenix.

```sql
SELECT first_attempt_site AS site FROM marts.fct_lead_journey WHERE EXTRACT(YEAR FROM created_date) = 2025 AND EXTRACT(MONTH FROM created_date) = 6 GROUP BY first_attempt_site ORDER BY AVG(speed_to_lead_business_minutes) ASC LIMIT 1
```

**q14. What was the conversion rate for leads first dialed within 5 business minutes, January to June 2025?** — wrong value. Answer 0.1086, gold 0.123889.

```sql
SELECT conversion_rate FROM marts.mart_monthly_kpis WHERE report_month BETWEEN '2025-01-01' AND '2025-06-30'
```

**q19. What was our first-contact resolution rate from January to June 2025?** — wrong value. Trap: FCR is outcome-based (no repeat within 7 days) and excludes contacts younger than 7 days; the agent's resolved flag overstates it. Answer 0.8285, gold 0.825307.

```sql
SELECT fcr_rate FROM marts.mart_monthly_kpis WHERE report_month BETWEEN '2025-01-01' AND '2025-06-30' LIMIT 1
```

**q21. What share of bot sessions actually resolved the customer's issue, January to June 2025?** — wrong value. Trap: Containment is not resolution; the answer must require containment and no repeat, over observable sessions. Answer 0.726395, gold 0.60455.

```sql
SELECT CAST(SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END) AS REAL) / COUNT(*) AS bot_resolution_rate FROM marts.fct_contacts WHERE contact_date BETWEEN '2025-01-01' AND '2025-06-30' AND started_with_bot = TRUE;
```

**q22. Which contact driver (most detailed level) has the lowest bot true resolution rate?** — false refusal. 

```sql
SELECT driver_path AS contact_driver, MIN(fcr_true_resolution_rate) AS lowest_fcr_true_resolution_rate FROM marts.fct_contacts JOIN marts.dim_contact_driver ON marts.fct_contacts.intent_code = marts.dim_contact_driver.intent_code GROUP BY driver_path ORDER BY lowest_fcr_true_resolution_rate ASC LIMIT 1
```

**q23. What was the repeat contact rate from January to June 2025?** — false refusal. 

```sql
SELECT AVG(repeat_contact_rate) AS repeat_contact_rate FROM marts.mart_monthly_kpis WHERE report_month BETWEEN '2025-01-01' AND '2025-06-30'
```

**q27. Which top-level contact driver category had the most contacts from January to June 2025?** — execution error. 

```sql
SELECT driver_l1 AS top_level_contact_driver FROM marts.dim_contact_driver WHERE started_at_local BETWEEN '2025-01-01' AND '2025-06-30' GROUP BY driver_l1 ORDER BY COUNT(*) DESC LIMIT 1
```

**q28. What was the resolution rate for Billing contacts (all channels), January to June 2025?** — wrong value. Answer 0.515705, gold 0.708198.

```sql
SELECT SUM(CASE WHEN entry_channel IN ('bot', 'chat', 'voice') THEN 1 ELSE 0 END) / COUNT(*) AS resolution_rate FROM marts.fct_contacts WHERE contact_date BETWEEN '2025-01-01' AND '2025-06-30' AND is_resolved = TRUE
```


## Where the governed agent went wrong

**q03. What was the lead conversion rate for leads created in Q2 2025?** — execution error. Request: `{"metrics": ["conversion_rate"], "group_by": ["metric_time__quarter"], "where": [{"dimension": "metric_time__quarter", "op": "=", "value": "Q2"}, {"dimension": "metric_time__year", "op": "=", "value": "2025"}], "start": "2025-04-01", "end": "2025-06-30", "order_by": {"metric": "conversion_rate", "desc": true}, "limit": 1}` Error: SemanticError: metric_time__quarter filter value 'Q2' is not a date. Time filters take the period's start date as YYYY-MM-DD (e.g. 2025-04-01 for April or for Q2 2025); for a date range use start and end.

**q05. What was the lead cost per sale for Clickstream Media from 15 March to 30 June 2025?** — execution error. Request: `{"metrics": ["cost_per_sale_usd"], "group_by": ["vendor__vendor_name"], "where": [{"dimension": "vendor__vendor_name", "op": "=", "value": "Clickstream Media"}, {"dimension": "metric_time__month", "op": "in", "value": ["2025-03", "2025-04", "2025-05", "2025-06"]}], "start": "2025-03-15", "end": "2025-06-30", "order_by": {"metric": "cost_per_sale_usd", "desc": false}, "limit": 1}` Error: SemanticError: metric_time__month filter value '2025-03' is not a date. Time filters take the period's start date as YYYY-MM-DD (e.g. 2025-04-01 for April or for Q2 2025); for a date range use start and end.

**q06. Which paid lead vendor had the highest lead cost per sale from 15 March to 30 June 2025?** — execution error. Request: `{"metrics": ["cost_per_sale_usd"], "group_by": ["vendor__vendor_name"], "where": [{"dimension": "metric_time__start", "op": ">=", "value": "2025-03-15"}, {"dimension": "metric_time__end", "op": "<=", "value": "2025-06-30"}], "order_by": {"metric": "cost_per_sale_usd", "desc": true}, "limit": 1}` Error: SemanticError: dimension 'metric_time__start' is not available for cost_per_sale_usd. Valid: metric_time__day, metric_time__month, metric_time__quarter, metric_time__week, metric_time__year, vendor__vendor_name

**q14. What was the conversion rate for leads first dialed within 5 business minutes, January to June 2025?** — no answer. Request: `{"metrics": ["conversion_rate"], "group_by": ["lead__speed_to_lead_band"], "where": [{"dimension": "lead__speed_to_lead_band", "op": "=", "value": "5 business minutes"}], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "conversion_rate", "desc": true}, "limit": 1}`

**q19. What was our first-contact resolution rate from January to June 2025?** — wrong value. Answer 0.828006, gold 0.825307. Request: `{"metrics": ["fcr_rate"], "group_by": ["metric_time__quarter"], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "fcr_rate", "desc": true}, "limit": 1}`

**q23. What was the repeat contact rate from January to June 2025?** — wrong value. Answer 0.196246, gold 0.203179. Request: `{"metrics": ["repeat_contact_rate"], "group_by": ["metric_time__quarter"], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "repeat_contact_rate", "desc": false}, "limit": 1}`

**q26. What share of contacting customers cancelled within 30 days of the contact, January to June 2025?** — execution error. Request: `{"metrics": ["churn_after_contact_rate"], "group_by": ["metric_time__quarter"], "where": [{"dimension": "metric_time__month", "op": "in", "value": "2025-01-01,2025-02-01,2025-03-01,2025-04-01,2025-05-01,2025-06-01"}], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "churn_after_contact_rate", "desc": true}, "limit": 1}` Error: SemanticError: metric_time__month filter value '2025-01-01,2025-02-01,2025-03-01,2025-04-01,2025-05-01,2025-06-01' is not a date. Time filters take the period's start date as YYYY-MM-DD (e.g. 2025-04-01 for April or for Q2 2025); for a date range use start and end.

**q28. What was the resolution rate for Billing contacts (all channels), January to June 2025?** — no answer. Request: `{"metrics": ["resolution_rate"], "group_by": ["contact__entry_channel"], "where": [{"dimension": "contact__entry_channel", "op": "=", "value": "Billing"}], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "resolution_rate", "desc": true}, "limit": 1}`

**q31. How many agent-handled contacts ended in the Tech Support queue in March 2025?** — wrong value. Answer 603, gold 502. Request: `{"metrics": ["agent_handled_contacts"], "group_by": ["contact__last_queue_name"], "where": [{"dimension": "metric_time__month", "op": "=", "value": "2025-03-01"}], "start": "2025-03-01", "end": "2025-03-31", "order_by": {"metric": "agent_handled_contacts", "desc": true}, "limit": 1}`

**q32. What was schedule adherence for Phoenix agents in Q1 2025?** — execution error. Request: `{"metrics": ["schedule_adherence"], "group_by": ["agent_day__site"], "where": [{"dimension": "agent_day__site", "op": "=", "value": "Phoenix"}, {"dimension": "metric_time__month", "op": ">=", "value": "2025-01-01"}, {"dimension": "metric_time__month", "op": "<=", "value": "2025-03-31"}], "start": "2025-01-01", "end": "2025-03-31", "order_by": {"metric": "schedule_adherence", "desc": true}, "limit": 1}` Error: SemanticError: filter operator '>=' not supported (use = or in, or start/end for ranges)

**q34. How many sales per paid hour did tier 1 agents make from January to June 2025?** — no answer. Request: `{"metrics": ["sales_per_paid_hour"], "group_by": ["agent_day__tier"], "where": [{"dimension": "agent_day__tier", "op": "=", "value": "tier_1"}, {"dimension": "metric_time__month", "op": "in", "value": ["2025-01-01", "2025-02-01", "2025-03-01", "2025-04-01", "2025-05-01", "2025-06-01"]}], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "sales_per_paid_hour", "desc": true}, "limit": 1}`

**q35. Which site had the lower schedule adherence from January to June 2025?** — wrong value. Answer Tampa, gold Phoenix. Request: `{"metrics": ["schedule_adherence"], "group_by": ["agent_day__site"], "start": "2025-01-01", "end": "2025-06-30", "order_by": {"metric": "schedule_adherence", "desc": true}, "limit": 1}`

