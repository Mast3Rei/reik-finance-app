<script>
    import { onMount, tick } from "svelte";
    import { chart } from "svelte-apexcharts";
    import axios from "axios";
    // import { spendLimit } from "../../account-store.js";

    let spend_limit = $state(0);

    let { dynamoDBData } = $props();// export let dynamoDBData;
    // export let spendLimit;
    let spendMarker = [];
    let show_chart = $state(false); //makes sure all data is loaded within component before display
    

    onMount(async () => {
        const id = '0'; //id of the spend limit (should go in the backend)
		const response = await axios.post('http://127.0.0.1:8000/reik_finance_app/bankaccountgetitem', {
			record_id: id
		});
		spend_limit = response.data.spend_limit;
        console.log("Chart spend_limit value:", spend_limit);

        // setTimeout(async () => {
        for (let i = 0; i < dynamoDBData.length; i++) {
            spendMarker.push(spend_limit);
        }
        console.log("Chart spendMarker:", spendMarker);
        // }, 1000);
        
        await tick(); //waits for updated DOM before continuing
        show_chart = true;
    })
    
    
    
    let options = {
        chart: {
            type: "line",
        },
        stroke: {
            width: [5,3],
            dashArray: [0,5],
        },
        series: [
            {
                name: "spending",
                data: dynamoDBData,
            },
            {
                name: "spend limit",
                data: spendMarker,
            },
        ],
        
        // fill: {
        //         type: 'pattern',
        //         pattern: {
        //             style: 'verticalLines',
        //             width: 6,
        //             length: 6,
        //             strokeWidth: 2,
        //         },
        //     },
        
        xaxis: {
            categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan"],
        },
        
    };

</script>

{#if show_chart}
    <div use:chart={options}></div>
{/if}