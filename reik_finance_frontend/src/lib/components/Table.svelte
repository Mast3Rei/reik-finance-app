<script>
    import { onMount } from "svelte";
    import axios from "axios";
    // import '../../app.css';
    import { Button } from 'flowbite-svelte';
    import { Table, TableBody, TableBodyCell, TableBodyRow, TableHead, TableHeadCell } from "flowbite-svelte";
    

    let table_data = [];

    let category1 = {};
    let category2 = {};
    let category3 = {};

    async function getTransactionTableData() {

		//get current year and month for record_id
		const now = new Date();
		const year = now.getFullYear().toString(); //current year
		const month = String(now.getMonth() + 1).padStart(2, '0'); //months are 0 indexed and padstart adds a 0 in front if there is only 1 digit
		const date_key = year+month;


		//get the current month record from DynamoDB database
		const cat_response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {record_id: date_key});
		const top_categories = cat_response.data.top_categories;
		console.log("Top Categories:", top_categories);
		return top_categories;
	}

    onMount(async () => {
        
        table_data = await getTransactionTableData();

        let categories = [{}, {}, {}];
        for (let i = 0; i < categories.length; i++) {
            if (table_data[i.toString()]===undefined) {
                categories[i] = {'tran_category': 'None', 'tran_total': 0,'tran_count': 0,'tran_spt': 0}
            } else {
                categories[i] = table_data[i.toString()];
            }
        }

        category1 = categories[0];
        category2 = categories[1];
        category3 = categories[2];


    })
</script>

<Table striped={true} hoverable={true}>
    <TableHead class="bg-gray-500 text-white">
        <TableHeadCell>Category</TableHeadCell>
        <TableHeadCell>Total</TableHeadCell>
        <TableHeadCell>Trans.</TableHeadCell>
        <TableHeadCell>SPT</TableHeadCell>
    </TableHead>
    <TableBody>
        <TableBodyRow class="hover:bg-gray-200 text-gray-900">
            <TableBodyCell>{category1['tran_category']}</TableBodyCell>
            <TableBodyCell>${category1['tran_total']}</TableBodyCell>
            <TableBodyCell>{category1['tran_count']}</TableBodyCell>
            <TableBodyCell>${category1['tran_spt']}</TableBodyCell>
        </TableBodyRow>
        <TableBodyRow class="hover:bg-gray-200 text-gray-900">
            <TableBodyCell>{category2['tran_category']}</TableBodyCell>
            <TableBodyCell>${category2['tran_total']}</TableBodyCell>
            <TableBodyCell>{category2['tran_count']}</TableBodyCell>
            <TableBodyCell>${category2['tran_spt']}</TableBodyCell>
        </TableBodyRow>
        <TableBodyRow class="hover:bg-gray-200 text-gray-900">
            <TableBodyCell>{category3['tran_category']}</TableBodyCell>
            <TableBodyCell>${category3['tran_total']}</TableBodyCell>
            <TableBodyCell>{category3['tran_count']}</TableBodyCell>
            <TableBodyCell>${category3['tran_spt']}</TableBodyCell>
        </TableBodyRow>
    </TableBody>
</Table>

<!-- text-primary-600 -->

