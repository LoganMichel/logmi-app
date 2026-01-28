"""
Models for app_linktree - Linktree-style Link Directory with Statistics
"""
import uuid
from django.db import models


class Link(models.Model):
    """
    Represents a link to an external site or social network.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nom du lien")
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name="Utilisateur",
        null=True,
        blank=True
    )
    url = models.URLField(max_length=2048, verbose_name="URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="Icône",
        help_text="Classe CSS de l'icône (ex: fab fa-twitter)"
    )

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Lien'
        verbose_name_plural = 'Liens'

    def __str__(self):
        return self.name

    @property
    def total_clicks(self):
        """Total number of clicks on this link."""
        return self.stats.count()

    @property
    def qrcode_clicks(self):
        """Number of clicks via QR code."""
        return self.stats.filter(via_qrcode=True).count()


class LinkStat(models.Model):
    """
    Represents a single access/click on a link.
    Tracks device type, location, and QR code usage.
    """
    DEVICE_TYPES = [
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('desktop', 'Desktop'),
        ('unknown', 'Unknown'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    link = models.ForeignKey(
        Link,
        on_delete=models.CASCADE,
        related_name='stats',
        verbose_name="Lien"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        db_index=True,
        verbose_name="Date d'accès"
    )
    via_qrcode = models.BooleanField(default=False, verbose_name="Via QR Code")
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPES,
        default='unknown',
        verbose_name="Type d'appareil"
    )
    city = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Ville"
    )
    country = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Pays"
    )
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True,
        verbose_name="Adresse IP"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        verbose_name="User Agent"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Statistique de lien'
        verbose_name_plural = 'Statistiques de liens'

    def __str__(self):
        return f"{self.link.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Company(models.Model):
    """
    Represents a company/business associated with the user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nom de la société")
    address = models.TextField(blank=True, verbose_name="Adresse")
    siret = models.CharField(
        max_length=14,
        blank=True,
        verbose_name="SIRET",
        help_text="Numéro SIRET (14 chiffres)"
    )
    tva = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="N° TVA",
        help_text="Numéro de TVA intracommunautaire"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        ordering = ['name']
        verbose_name = 'Société'
        verbose_name_plural = 'Sociétés'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """
    Profile information for the linktree owner.
    One profile per Django User.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='linktree_profile',
        verbose_name="Utilisateur",
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Nom")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    companies = models.ManyToManyField(
        Company,
        blank=True,
        related_name='user_profiles',
        verbose_name="Sociétés"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateur'

    def __str__(self):
        if self.user:
            return f"Profil de {self.user.username}"
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return f"Profil {self.id}"

    @classmethod
    def get_profile_for_user(cls, user):
        """Get or create the profile for a specific user."""
        profile, _ = cls.objects.get_or_create(user=user)
        return profile

    def save(self, *args, **kwargs):
        """Auto-fill first_name, last_name, email from User if empty."""
        if self.user:
            if not self.first_name and self.user.first_name:
                self.first_name = self.user.first_name
            if not self.last_name and self.user.last_name:
                self.last_name = self.user.last_name
            if not self.email and self.user.email:
                self.email = self.user.email
        super().save(*args, **kwargs)

