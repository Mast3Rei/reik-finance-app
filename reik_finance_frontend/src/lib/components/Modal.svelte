<script>
    import { createEventDispatcher } from 'svelte';
    let {showModal = $bindable(), children} = $props();

    let dialog = $state();
    const dispatch = createEventDispatcher();

    $effect (() => {
        if (showModal) dialog.showModal();
    });
    // function closeModal() {
    //     showModal = false;
    // }
</script>


<dialog
    bind:this={dialog}
    onclose={() => dispatch('close')}
    onclick={(e) => {if (e.target === dialog) dialog.close(); }}
    >
    <div>
        {@render children?.()}
        <hr/>
        <button onclick={() => dialog.close()}>continue</button>
    </div>

</dialog>


<style>
    dialog {
        max-width: 32em;
        border-radius: 0.2em;
        border: none;
        padding: 0;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    dialog::backdrop {
        background: rgba(0,0,0,0.3);
    }

    dialog > div {
        padding: 1em;
    }

    dialog[open] {
		animation: zoom 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
	}

    @keyframes zoom {
        from {
            transform: scale(0.95);
        }
        to {
            transform: scale(1);
        }
    }

    dialog[open] {
        animation: fade 0.2s ease-out;
    }

    @keyframes fade {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    button {
        display: block;
    }

    hr {
        margin-top: 2em;
        margin-bottom: 2em;
        border-top: 2px solid #aaa;
        width: 100%;
    }
</style>