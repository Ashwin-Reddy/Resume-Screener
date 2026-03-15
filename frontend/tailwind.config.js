export default {
    content: [
        "./index.html",
        "./src/**/*.{js,jsx}",
    ],
    theme: {
        extend: {
            colors: {
                'bg-primary': '#F3F4F4',
                'box-primary': '#1D546D',
                'btn-primary': '#061E29',
            },
            fontFamily: {
                'archivo': ['Archivo Black', 'sans-serif'],
                'inter': ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}