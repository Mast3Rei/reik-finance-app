import { writable } from 'svelte/store';
import axios from 'axios';

export const bankAccount = writable([]);
export const spendLimit = writable(0);

async function fetchSpendLimit() {
		const id = '0'; //id of the spend limit (should go in the backend)
		const response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {
			record_id: id
		});
		spendLimit.set(response.data.spend_limit);
}
fetchSpendLimit();