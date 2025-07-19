<script>
	import { onMount, tick } from "svelte";
	import axios from "axios";
	import { bankAccount, spendLimit } from './account-store.js';
	import Chart from "./lib/components/Chart.svelte";
	import Table from "./lib/components/Table.svelte";
	import Modal from './lib/components/Modal.svelte';
	import './app.css';
	// import Plaid from "plaid";
	
	let { reikModels } = $props();

	let curr_month_spend = $state(0);
	let prev_month_spend = $state(0);
	let percentage_curr_month = $state(0);
	let financial_balance = $state('');
	let financial_acc_name = $state('');
	let savingsAccount = {};
	let checkingAccount = {};
	let creditAccount = {};
	let accessToken = ''; //this will be used for future API calls
	let transactions = {};
	let chart_data = [];
	let show_chart = $state(false); //when it becomes true the data for the Chart.svelte component will be ready to load
	let spend_limit = $state(null); //used to compare the target spending goal for the month
	// let spend_limit = $state(0);
	let showBankModal = $state(false);
	let showCreditModal = $state(false);
	let modalAction = null;
	let recoveryState = {bank: false, credit: false}; //indicates whether account has successfully gone through recovery process
	let recoveryQueue = []; //queue for processing relinks and unfinished actions
	let pendingActions = []; //any actions that need redos go here
	let recoveryInProgress = false; //used to prevent multiple relink launches at one time

	$effect(async () => {
		spendLimit.subscribe(async (value) => {
			spend_limit = await value;
			console.log("spend limit store value:", spend_limit);
		})
	})
	

	async function updateDatabase(access_token) {
			//get the sum amounts for this year-----------------------------------------------------
			
			await updateBankData(); //calls plaid API with access_token for bank data

			//get the transaction sums from plaid by the backend
			const record_curr = await updateTransactionsCurrMonth();
			const record_prev = await updateTransactionsPrevMonth();
			console.log("My record_curr & record_prev:", record_curr, record_prev);
			await updateLastUpdate(); //mark this date as the last updated time
		}

	async function updateSpendLimit(limit) {
		if (typeof spend_limit === 'number' && spend_limit > 0) {
			const post_data = {record_id: '0', spend_limit: limit}; //the spend_limit record id is always '0' as string
			console.log("update spend limit delay 0 seconds", post_data);
			await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountupdateitem', {
				record: post_data
			});
		};
	}
	
	async function updateBalance(balance) {
		const post_data = {record_id: '1', account_balance: balance};
		await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountputitem', {
			record: post_data
		});
	}

	async function updateBankData() {
		try {
			// accounts info
			const get_bank_account = await axios.get('http://127.0.0.1:8000/reik_finance_app/get-bank-account');

			const bankAccountData = get_bank_account.data.accounts;
			console.log('My bank account data:', bankAccountData);

			//extract the savings and checking data
			savingsAccount = bankAccountData.find(acc => acc.subtype == "savings");
			checkingAccount = bankAccountData.find(acc => acc.subtype == "checking");
			console.log("Savings account:", savingsAccount);
			console.log("Checking account:", checkingAccount);
			
			//update dynamoDB table with balance
			const update_balance = savingsAccount.balances['current'] + checkingAccount.balances['current'];
			await updateBalance(update_balance);

			financial_acc_name = savingsAccount.name;

		} catch (err) {
			const plaidError = err.response?.data?.error_code;
			const errors = ["ITEM_LOGIN_REQUIRED", "INVALID_ACCESS_TOKEN", "ITEM_ERROR"];
			if (errors.includes(plaidError)) {
				console.log("Plaid access error:", plaidError);
				await queueRecoveryAction('bank', updateBankData); //send unprocessed action to queue
				await processRecoveryQueue(); //begin process recovery
			} else {
				console.error('Unhandled error updateBankData: ', err);
			}
		} 
	}

	async function getLastUpdate() {
		const id = '0';
		const response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {
			record_id: id
		})
		const record = response.data.last_update;
		const date = record.split("/");
		const processed_date = {"month":date[0], "day":date[1], "year":date[2]};
		return processed_date;
	}

	function getCurrentDate() {
		//grab the current date mm/dd/yr
		const now = new Date();
		const year = now.getFullYear().toString();
		const month = String(now.getMonth() + 1).padStart(2,'0');
		const day = String(now.getDate() + 1).padStart(2,'0');

		const curr_date = month + '/' + day + '/' + year;
		return curr_date;
	}

	//ensure record_id is included in record
	async function updateLastUpdate() {
		const curr_date = getCurrentDate();
		const new_record = {'record_id': '0', 'last_update':curr_date};
		await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountupdateitem', {
			record: new_record
		});
	}

	async function getBalance() {
		const id = '1';
		const response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {
			record_id: id
		});
		return response.data;
	}

	//date1=earlier date, date2=later date
	function differenceInDays(date1, date2) {
		const ONE_DAY_MS = 1000 * 60 * 60 * 24;
		const d1 = new Date(date1);
		const d2 = new Date(date2);

		const diff_ms = Math.floor(d2.getTime() - d1.getTime());
		return Math.floor(diff_ms / ONE_DAY_MS);
	}

	function getCurrMonthDate() {
		//get current year and month for record_id
		const now = new Date();
		const year = now.getFullYear().toString(); //current year
		const month = String(now.getMonth() + 1).padStart(2, '0'); //months are 0 indexed and padstart adds a 0 in front if there is only 1 digit
		const date_key = year+month;
		return date_key;
	}

	function getPrevMonthDate() {
		const now = new Date();
		const prev_month = new Date(now.getFullYear(), now.getMonth() - 1); 

		const year = prev_month.getFullYear().toString();
		const month = String(prev_month.getMonth()+1).padStart(2, '0');

		const date_key = year+month;

		return date_key;
	}

	async function getCurrMonthRecord() {
		//get the date for record_id to extract record
		const id = getCurrMonthDate();

		console.log("CurrMonth Record ID:", id);
		const response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {
			record_id: id
		})

		return response.data;
	}

	async function getPrevMonthRecord() {
		
		const id = getPrevMonthDate();

		console.log("PrevMonth Record ID:", id);
		const response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {
			record_id: id
		})

		return response.data;
	}
	

	function getCurrentYearAmounts() {
		//get all the data of current year
		const year = new Date().getFullYear().toString(); //current year

		//Filter and sort data
		function checkId(item) {
			return item['all_data']['record_id'].slice(0,4) === year;
		};
		let new_data = reikModels.filter(checkId);
		new_data.sort((a,b) => a.all_data.record_id.localeCompare(b.all_data.record_id));

		//Gather the amount sums to load into chart
		chart_data.push(0); //adds a starting value
		new_data.forEach(element => {
			const c_data = element.all_data.amount_sum;
			chart_data.push(c_data);
		});

		console.log("Chart data pulled from AWS DynamoDB table");
	}

	async function loadChart() {
		getCurrentYearAmounts();
		//wait for svelte to update the DOM
		await tick();
		show_chart = true;
	}

	//ONMOUNT
	onMount(async () => {
		const response = await axios.get('http://127.0.0.1:8000/reik_finance_app/bankaccount');
		bankAccount.set(response.data); // also can write reikModels = response.data;
		console.log("DynamoDB response:", response.data);
		bankAccount.subscribe((value) => {
			reikModels = value;
		})

		await loadChart(); //load current year transaction sums and save to chart_data to load to chart

		// grab the balance from dynamoDB
		//balance and account name
		financial_balance = await getBalance();
		financial_balance = financial_balance.account_balance;

		//get the current month spend and previous month spend
		const curr_month_record = await getCurrMonthRecord();
		const prev_month_record = await getPrevMonthRecord();
		curr_month_spend = curr_month_record.amount_sum;
		prev_month_spend = prev_month_record.amount_sum;

		changeColorCurrMonth();
		changeColorPrevMonth();

		console.log("CurrMonth Record:", curr_month_spend);
		console.log("PrevMonth Record:", prev_month_spend);
		
		//set the percentage of current month
		percentage_curr_month = Math.round((curr_month_spend/spend_limit)*100);
		
		console.log("Financial balances:", financial_balance);


		//check last update

		
		const last_update_date = await getLastUpdate();

		const prev_date  = last_update_date.year + '-' + last_update_date.month + '-' + last_update_date.day;
		const curr_date = getCurrentDate();
		const diff_date = differenceInDays(prev_date, curr_date);
		if (diff_date >= 3) {
			await updateDatabase();
		}
	});


	//buttons and boxes
	let financial_status_current = $state('spending-good'); //good, medium, bad
	let financial_status_previous = $state('spending-good');
	let setting = 0; //CHANGE THIS AS INPUT

	
	$effect(async () => {
		updateSpendLimit(spend_limit);
		console.log("spend_limit saved:", spend_limit);
	});

	async function getBankFinancialData() {
		//Bank Account Plaid section
		const res = await axios.post('http://127.0.0.1:8000/reik_finance_app/create-link-token', {
				user_id:'reik123',
			}
		); 
		const link_data = res.data;
		const linkToken = link_data.link_token;
		console.log("This is my Plaid: ", Plaid);
		const handler = Plaid.create({
			token: linkToken,
			// env: 'sandbox', //take this out for dev/prod mode
			onSuccess: async (public_token, metadata) => {
				console.log("public_token", public_token);
				console.log(public_token ? "Public token received. Exchange in progress" : "Error with public token");

				// Here I will make one exchange token for bank account and another for credit account
				//exchange request
				const exchangeBankToken = await axios.post('http://127.0.0.1:8000/reik_finance_app/exchange-public-token-bank', {
					public_token: public_token
				});

				recoveryState.bank = true; //the bank account has been recovered
				await triggerActionsRedo(); //triggers any actions that are pending
				await processRecoveryQueue(); //runs recovery queue again to check for unprocessed queue requests
			}
			
		});
		handler.open();
	}

	async function getCreditFinancialData() {
		//Bank Account Plaid section
		const res = await axios.post('http://127.0.0.1:8000/reik_finance_app/create-link-token', {
				user_id:'reik123',
			}
		); 
		const link_data = res.data;
		const linkToken = link_data.link_token;

		const handler = Plaid.create({
			token: linkToken,
			// env: 'sandbox', //take this out for dev/prod mode
			onSuccess: async (public_token, metadata) => {
				console.log("public_token", public_token);
				console.log(public_token ? "Public token received. Exchange in progress" : "Error with public token");

				const exchangeCreditToken = await axios.post('http://127.0.0.1:8000/reik_finance_app/exchange-public-token-credit', {
					public_token: public_token	
				});

				const get_credit_account = await axios.get('http://127.0.0.1:8000/reik_finance_app/get-credit-account');
				const creditAccountData = get_credit_account.data.accounts;
				console.log('My credit card account data', creditAccountData);

				creditAccount = creditAccountData.find(acc => acc.subtype == "credit card"); // change this for production; 2 different accountsData
				console.log("Credit card account info:", creditAccount);

				recoveryState.credit = true; //the credit card account has been recovered
				await triggerActionsRedo(); //triggers any actions that are pending
				await processRecoveryQueue(); //runs recovery queue again to check for unprocessed queue requests
				
			}
		});
		handler.open();
	}

	function changeColorCurrMonth() {
		console.log("ColorCurrMonth spend_limit, curr_month_spend, and financial_status_current:", spend_limit, curr_month_spend, financial_status_current);

		const spendLimit = Number(spend_limit);
		const monthSpend = Number(curr_month_spend);
		if (monthSpend <= spendLimit) {
			financial_status_current = 'spending-good';
		}
		else if (monthSpend <= (spendLimit+(spendLimit*0.2)) && monthSpend > spendLimit) { //506 > 400 and 506 <= 480
			financial_status_current = 'spending-med';
		}
		else {
			financial_status_current = 'spending-bad';
		}

		console.log("ColorCurrMonth financial_status_curr result:", financial_status_current);
	}

	function changeColorPrevMonth() {
		const spendLimit = Number(spend_limit);
		const prevMonthSpend = Number(prev_month_spend);

		if (prevMonthSpend <= spendLimit) {
			financial_status_previous = 'spending-good';
		}
		else if (prevMonthSpend <= (spendLimit+(spendLimit*0.2)) && prevMonthSpend > spendLimit) { //506 > 400 and 506 <= 480
			financial_status_previous = 'spending-med';
		}
		else {
			financial_status_previous = 'spending-bad';
		}
	}

	function getYearMonth(t_data) {
		const amount_date = t_data['0'].date.split("-")['0'] + "-" + t_data['0'].date.split("-")['1']; //year-month
		const record_id = t_data['0'].date.split("-")['0'] + t_data['0'].date.split("-")['1'];
		return {"amount_date":amount_date, "record_id":record_id};
	}


	async function triggerActionsRedo() {
		for (const action of pendingActions) {
			await action();
		}
		pendingActions = [];
		recoveryInProgress = false;
	}

	//pushes unprocessed requests to a queue by type and action
	async function queueRecoveryAction(type, action) {
		const alreadyQueued = recoveryQueue.some(item => item.action.name === action.name && item.type === type);
		if (!alreadyQueued) {
			recoveryQueue.push({type:type, action:action,});
		}
	}

	//takes unprocessed requests and identifies if a relink is required and uploads the action to pendingActions list
	async function processRecoveryQueue() {
		if (!recoveryInProgress) {
			for (const recovery of recoveryQueue) {
				//if type not recovered yet run first block
				if(!recoveryState[recovery.type]) {
					pendingActions.push(recovery.action); //push action to pendingActions for redo
					recoveryInProgress = true; //initiate recovery in progress to prevent multiple relink launches at one time
					await (recovery.type === 'bank' ? handleBankLink() : handleCreditLink()); //run the requested relink
					break; //prevent launching multiple modals at a time
				}
				//if type already recovered and the action not already included in pendingActions, run second block
				else if (recoveryState[recovery.type] && !pendingActions.some(item => item.name === recovery.action.name)){
					pendingActions.push(recovery.action);
				}
			}
		}
		
	}


	async function updateTransactionsCurrMonth() {
		try {
			//transactions
			const get_transactions = await axios.get('http://127.0.0.1:8000/reik_finance_app/get-transactions-curr-month');

			const transaction_data = get_transactions.data.transactions;
			console.log("Transactions data:", transaction_data);

			const group_transactions = await axios.post('http://127.0.0.1:8000/reik_finance_app/group-transactions', {transactions:transaction_data});
			const total_transactions = group_transactions.data;
			console.log("Group transaction data:", total_transactions);
			const curr_month_spend = total_transactions.amount;
			changeColorCurrMonth();
			

			//return necessary data to store in database
			const amount_date = getYearMonth(transaction_data)['amount_date'];
			const record_id = getYearMonth(transaction_data)['record_id'];
			// console.log("My transaction data date:", amount_date);

			const top_categories = await getTransactionCategories(transaction_data); //TEST

			console.log("Print curr month top_categories:", top_categories);

			//update database with record
			const record_curr = {"record_id": record_id, 'amount_sum':curr_month_spend, 'amount_date': amount_date, 'top_categories':top_categories};
			await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountputitem', {
				record: record_curr
			});
			return record_curr;

		} catch (err) {
			const plaidError = err.response?.data?.error_code;
			const errors = ["ITEM_LOGIN_REQUIRED", "INVALID_ACCESS_TOKEN", "ITEM_ERROR"];
			if (errors.includes(plaidError)) {
				console.log("Plaid access error:", plaidError);
				await queueRecoveryAction('credit', updateTransactionsCurrMonth); //send unprocessed action to queue
				await processRecoveryQueue(); //begin process recovery
			} else {
				console.error('Unhandled error updateTransactionsCurrMonth: ', err);
			}
		}
	}

	async function updateTransactionsPrevMonth() {
		try {
			//transactions
			const get_transactions = await axios.get('http://127.0.0.1:8000/reik_finance_app/get-transactions-prev-month');

			const transaction_data = get_transactions.data.transactions;
			console.log("Transactions data prev month:", transaction_data);

			const group_transactions = await axios.post('http://127.0.0.1:8000/reik_finance_app/group-transactions', {transactions:transaction_data});
			const total_transactions = group_transactions.data;
			console.log("Group transaction data prev month:", total_transactions);
			const prev_month_spend = total_transactions.amount;
			changeColorPrevMonth();

			//return necessary data to store in database
			const amount_date = getYearMonth(transaction_data)['amount_date'];
			const record_id = getYearMonth(transaction_data)['record_id'];

			const top_categories = await getTransactionCategories(transaction_data); //TEST

			//update database with record
			const record_prev = {"record_id": record_id, 'amount_sum':prev_month_spend, 'amount_date': amount_date, 'top_categories':top_categories};
			await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountputitem', {
				record: record_prev
			});
			return record_prev;
			
		} catch (err) {
			const plaidError = err.response?.data?.error_code;
			const errors = ["ITEM_LOGIN_REQUIRED", "INVALID_ACCESS_TOKEN", "ITEM_ERROR"]
			if (errors.includes(plaidError)) {
				console.log("Plaid access error:", plaidError);
				await queueRecoveryAction('credit', updateTransactionsPrevMonth); //send unprocessed action to queue
				await processRecoveryQueue(); //begin process recovery
			} else {
				console.error('Unhandled error updateTransactionsPrevMonth: ', err);
			}
		}
	}

	//Get transaction data. This function will return 3 top categories
	async function getTransactionCategories(tran_data) {
		// record_id: year-month, date: year-month, trans amount, category

		const t_id = getYearMonth(tran_data)['record_id'];
		const t_date = getYearMonth(tran_data)['amount_date'];


		function capitalizeFirstLetter(val) {
			return String(val).charAt(0).toUpperCase() + String(val).slice(1);
		}
		//filtering the transactions so top categories can be extracted
		let filtered_transactions = [];
		for (let i = 0; i < tran_data.length; i++) {
			const t_amount = tran_data[i.toString()]['amount'];
			let t_cat = (tran_data[i.toString()]['personal_finance_category']['primary'].toLowerCase()).split("_");
			t_cat = capitalizeFirstLetter(t_cat.join(" "));
			filtered_transactions.push({'record_id':t_id, 'amount_date': t_date, 'amount':t_amount, 'category':t_cat});
		}

		const categories = await axios.post('http://127.0.0.1:8000/reik_finance_app/get-transaction-categories', filtered_transactions);
		const cat_data = categories.data.categories;
		console.log("Categories:", cat_data);

		return cat_data;
	}


	//MODAL Section
	async function handleBankLink() {
		modalAction = getBankFinancialData;
		showBankModal = true;
	}
	async function handleCreditLink() {
		modalAction = getCreditFinancialData;
		showCreditModal = true;
	}

	async function onModalClose() {
		showBankModal = false;
		showCreditModal = false;
		if (typeof modalAction === 'function') {
			await modalAction();
			modalAction = null; // reset
		}
	}

</script>

<main>

	<Modal bind:showModal={showBankModal} on:close={onModalClose}> <h2>Log in to your <strong>bank</strong> account</h2> </Modal>
	<Modal bind:showModal={showCreditModal} on:close={onModalClose}> <h2>Log in to your <strong>credit card</strong> account</h2> </Modal>

	<div class="container">
		<div class="small-box">total balance<br><h3>${financial_balance}</h3></div>
		<div class="small-box {financial_status_current}">spent this month<br><h3>${curr_month_spend}</h3></div>
		<div class="small-box {financial_status_current}">percentage to limit<br><h3>%{percentage_curr_month}</h3></div>
		<div class="small-box {financial_status_previous}">spent last month<br><h3>${prev_month_spend}</h3></div>
	</div>

	<hr/>
	
	<div class="container">
		
		<div class="chart">
			{#if show_chart}
			<Chart dynamoDBData={chart_data}/>
			{/if}
		</div>
		
		<div style="max-height: none; overflow: visible;">
			<label>
				<h4>Spending Limit : <input type="number" bind:value={spend_limit} min="0" max="999999" /></h4>
			</label>
			<Table/>
		</div>
	</div>
	
</main>

<style>
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}

	h1 {
		color: #ff3e00;
		font-size: 4em;
		font-weight: 100;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}

	/* Buttons and boxes */
	.box {
		margin: auto;
		width: 900px;
		height: 100px;
		border: 2px solid black;
	}

	.container {
		display:flex;
		justify-content: space-between;
		align-items: center;
		flex: 1;
	}

	.chart {
		margin: auto;
		width: 50%;
		height: auto;
	}

	.small-box {
		width: 200px;
		height: 100px;
		border: 2px solid black;
	}

	.spending-good {
		background-color:green;
	}
	.spending-med {
		background-color: yellow;
	}
	.spending-bad {
		background-color:red;
	}

	hr {
        margin-top: 2em;
        margin-bottom: 2em;
        border-top: 2px solid #aaa;
        width: 100%;
    }

	
</style>