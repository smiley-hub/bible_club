from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label='Your name', max_length=100, widget=forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Your name'}))
    email = forms.EmailField(label='Email address', max_length=254, widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'you@example.com'}))
    topic = forms.ChoiceField(label='What would you like to ask about?', choices=[('visit', 'Visiting a gathering'), ('location', 'Finding the meeting place'), ('community', 'Getting involved'), ('other', 'Something else')])
    message = forms.CharField(label='Your message', min_length=10, max_length=5000, widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'Tell us a little more...'}))
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        if self.cleaned_data['website']:
            raise forms.ValidationError('Please leave this field empty.')
        return ''
