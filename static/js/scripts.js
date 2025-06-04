// Main JavaScript file for client-side functionality

document.addEventListener('DOMContentLoaded', function() {
    // YouTube URL validation
    const youtubeForm = document.querySelector('form');
    if (youtubeForm) {
        youtubeForm.addEventListener('submit', function(event) {
            const urlInput = document.getElementById('youtube_url');
            if (urlInput) {
                const url = urlInput.value.trim();
                const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)[a-zA-Z0-9_-]{11}(\S*)?$/;
                
                if (!youtubeRegex.test(url)) {
                    event.preventDefault();
                    alert('Please enter a valid YouTube URL. Example: https://www.youtube.com/watch?v=xxxxxxxxxx');
                    urlInput.focus();
                }
            }
        });
    }
    
    // Auto-scroll functionality for lyrics boxes
    const lyricsBoxes = document.querySelectorAll('.lyrics-box');
    lyricsBoxes.forEach(box => {
        if (box.scrollHeight > box.clientHeight) {
            // Add a small indicator that content is scrollable
            box.classList.add('is-scrollable');
        }
    });
    
    // Show alert if browser doesn't support clipboard API
    const copyButtons = document.querySelectorAll('[onclick^="copyToClipboard"]');
    if (copyButtons.length > 0 && !navigator.clipboard) {
        copyButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                alert('Your browser does not support automatic copying. Please select the text and copy manually (Ctrl+C / Cmd+C).');
            });
        });
    }
}); 