.class public final Lcom/gramforge/NotInterestedTapper;
.super Ljava/lang/Object;
.source "NotInterestedTapper.java"


# static fields
.field private static final TAG:Ljava/lang/String; = "GramForge"

.field private static final TARGET:Ljava/lang/String; = "Not interested"


# direct methods
.method private constructor <init>()V
    .locals 0

    .line 20
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method static synthetic access$000(Landroid/view/View;)Z
    .locals 0

    .line 17
    invoke-static {p0}, Lcom/gramforge/NotInterestedTapper;->tap(Landroid/view/View;)Z

    move-result p0

    return p0
.end method

.method private static activityOf(Landroid/content/Context;)Landroid/app/Activity;
    .locals 2

    .line 44
    const/4 v0, 0x0

    :goto_0
    const/16 v1, 0xc

    if-ge v0, v1, :cond_3

    if-eqz p0, :cond_3

    .line 45
    instance-of v1, p0, Landroid/app/Activity;

    if-eqz v1, :cond_0

    check-cast p0, Landroid/app/Activity;

    return-object p0

    .line 46
    :cond_0
    instance-of v1, p0, Landroid/content/ContextWrapper;

    if-nez v1, :cond_1

    goto :goto_1

    .line 47
    :cond_1
    move-object v1, p0

    check-cast v1, Landroid/content/ContextWrapper;

    invoke-virtual {v1}, Landroid/content/ContextWrapper;->getBaseContext()Landroid/content/Context;

    move-result-object v1

    .line 48
    if-ne v1, p0, :cond_2

    goto :goto_1

    .line 49
    :cond_2
    nop

    .line 44
    add-int/lit8 v0, v0, 0x1

    move-object p0, v1

    goto :goto_0

    .line 51
    :cond_3
    :goto_1
    const/4 p0, 0x0

    return-object p0
.end method

.method private static call(Ljava/lang/Object;Ljava/lang/String;)Ljava/lang/Object;
    .locals 4

    .line 55
    const/4 v0, 0x0

    if-nez p0, :cond_0

    return-object v0

    .line 57
    :cond_0
    :try_start_0
    invoke-virtual {p0}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object v1

    const/4 v2, 0x0

    new-array v3, v2, [Ljava/lang/Class;

    invoke-virtual {v1, p1, v3}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object p1

    .line 58
    new-array v1, v2, [Ljava/lang/Object;

    invoke-virtual {p1, p0, v1}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object p0
    :try_end_0
    .catch Ljava/lang/ReflectiveOperationException; {:try_start_0 .. :try_end_0} :catch_1
    .catch Ljava/lang/SecurityException; {:try_start_0 .. :try_end_0} :catch_0

    return-object p0

    .line 59
    :catch_0
    move-exception p0

    goto :goto_0

    :catch_1
    move-exception p0

    .line 60
    :goto_0
    return-object v0
.end method

.method private static scanManager(Ljava/lang/Object;I)Z
    .locals 5

    .line 75
    const/4 v0, 0x4

    const/4 v1, 0x0

    if-le p1, v0, :cond_0

    return v1

    .line 76
    :cond_0
    const-string v0, "getFragments"

    invoke-static {p0, v0}, Lcom/gramforge/NotInterestedTapper;->call(Ljava/lang/Object;Ljava/lang/String;)Ljava/lang/Object;

    move-result-object p0

    .line 77
    instance-of v0, p0, Ljava/util/List;

    if-nez v0, :cond_1

    return v1

    .line 78
    :cond_1
    check-cast p0, Ljava/util/List;

    invoke-interface {p0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    move-result-object p0

    :goto_0
    invoke-interface {p0}, Ljava/util/Iterator;->hasNext()Z

    move-result v0

    if-eqz v0, :cond_5

    invoke-interface {p0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v0

    .line 79
    if-nez v0, :cond_2

    goto :goto_0

    .line 80
    :cond_2
    const-string v2, "getDialog"

    invoke-static {v0, v2}, Lcom/gramforge/NotInterestedTapper;->call(Ljava/lang/Object;Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v2

    .line 81
    instance-of v3, v2, Landroid/app/Dialog;

    const/4 v4, 0x1

    if-eqz v3, :cond_3

    .line 82
    check-cast v2, Landroid/app/Dialog;

    invoke-virtual {v2}, Landroid/app/Dialog;->getWindow()Landroid/view/Window;

    move-result-object v2

    .line 83
    if-eqz v2, :cond_3

    invoke-virtual {v2}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    move-result-object v2

    invoke-static {v2, v1}, Lcom/gramforge/NotInterestedTapper;->scanView(Landroid/view/View;I)Z

    move-result v2

    if-eqz v2, :cond_3

    return v4

    .line 85
    :cond_3
    const-string v2, "getChildFragmentManager"

    invoke-static {v0, v2}, Lcom/gramforge/NotInterestedTapper;->call(Ljava/lang/Object;Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    .line 86
    if-eqz v0, :cond_4

    add-int/lit8 v2, p1, 0x1

    invoke-static {v0, v2}, Lcom/gramforge/NotInterestedTapper;->scanManager(Ljava/lang/Object;I)Z

    move-result v0

    if-eqz v0, :cond_4

    return v4

    .line 87
    :cond_4
    goto :goto_0

    .line 88
    :cond_5
    return v1
.end method

.method private static scanView(Landroid/view/View;I)Z
    .locals 5

    .line 92
    const/4 v0, 0x0

    if-eqz p0, :cond_6

    const/16 v1, 0x1e

    if-gt p1, v1, :cond_6

    invoke-virtual {p0}, Landroid/view/View;->isShown()Z

    move-result v1

    if-nez v1, :cond_0

    goto :goto_3

    .line 93
    :cond_0
    instance-of v1, p0, Landroid/widget/TextView;

    const/4 v2, 0x1

    if-eqz v1, :cond_3

    .line 94
    move-object v1, p0

    check-cast v1, Landroid/widget/TextView;

    invoke-virtual {v1}, Landroid/widget/TextView;->getText()Ljava/lang/CharSequence;

    move-result-object v1

    .line 95
    if-eqz v1, :cond_3

    invoke-interface {v1}, Ljava/lang/CharSequence;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object v1

    const-string v3, "Not interested"

    invoke-virtual {v3, v1}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v1

    if-eqz v1, :cond_3

    .line 96
    nop

    .line 97
    move-object v3, p0

    const/4 v1, 0x0

    :goto_0
    const/4 v4, 0x5

    if-ge v1, v4, :cond_3

    if-eqz v3, :cond_3

    .line 98
    invoke-virtual {v3}, Landroid/view/View;->isClickable()Z

    move-result v4

    if-eqz v4, :cond_1

    invoke-virtual {v3}, Landroid/view/View;->isEnabled()Z

    move-result v4

    if-eqz v4, :cond_1

    .line 99
    invoke-virtual {v3}, Landroid/view/View;->performClick()Z

    .line 100
    return v2

    .line 102
    :cond_1
    invoke-virtual {v3}, Landroid/view/View;->getParent()Landroid/view/ViewParent;

    move-result-object v3

    .line 103
    instance-of v4, v3, Landroid/view/View;

    if-eqz v4, :cond_2

    check-cast v3, Landroid/view/View;

    goto :goto_1

    :cond_2
    const/4 v3, 0x0

    .line 97
    :goto_1
    add-int/lit8 v1, v1, 0x1

    goto :goto_0

    .line 107
    :cond_3
    instance-of v1, p0, Landroid/view/ViewGroup;

    if-eqz v1, :cond_5

    .line 108
    check-cast p0, Landroid/view/ViewGroup;

    .line 109
    const/4 v1, 0x0

    :goto_2
    invoke-virtual {p0}, Landroid/view/ViewGroup;->getChildCount()I

    move-result v3

    if-ge v1, v3, :cond_5

    .line 110
    invoke-virtual {p0, v1}, Landroid/view/ViewGroup;->getChildAt(I)Landroid/view/View;

    move-result-object v3

    add-int/lit8 v4, p1, 0x1

    invoke-static {v3, v4}, Lcom/gramforge/NotInterestedTapper;->scanView(Landroid/view/View;I)Z

    move-result v3

    if-eqz v3, :cond_4

    return v2

    .line 109
    :cond_4
    add-int/lit8 v1, v1, 0x1

    goto :goto_2

    .line 113
    :cond_5
    return v0

    .line 92
    :cond_6
    :goto_3
    return v0
.end method

.method public static schedule(Landroid/view/View;)V
    .locals 2

    .line 23
    if-nez p0, :cond_0

    return-void

    .line 24
    :cond_0
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    .line 25
    new-instance v1, Lcom/gramforge/NotInterestedTapper$1;

    invoke-direct {v1, p0, v0}, Lcom/gramforge/NotInterestedTapper$1;-><init>(Landroid/view/View;Landroid/os/Handler;)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 41
    return-void
.end method

.method private static tap(Landroid/view/View;)Z
    .locals 3

    .line 65
    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;

    move-result-object p0

    invoke-static {p0}, Lcom/gramforge/NotInterestedTapper;->activityOf(Landroid/content/Context;)Landroid/app/Activity;

    move-result-object p0

    .line 66
    const/4 v0, 0x0

    if-nez p0, :cond_0

    return v0

    .line 67
    :cond_0
    const-string v1, "getSupportFragmentManager"

    invoke-static {p0, v1}, Lcom/gramforge/NotInterestedTapper;->call(Ljava/lang/Object;Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v1

    .line 68
    invoke-static {v1, v0}, Lcom/gramforge/NotInterestedTapper;->scanManager(Ljava/lang/Object;I)Z

    move-result v1

    const/4 v2, 0x1

    if-eqz v1, :cond_1

    return v2

    .line 70
    :cond_1
    invoke-virtual {p0}, Landroid/app/Activity;->getWindow()Landroid/view/Window;

    move-result-object p0

    .line 71
    if-eqz p0, :cond_2

    invoke-virtual {p0}, Landroid/view/Window;->getDecorView()Landroid/view/View;

    move-result-object p0

    invoke-static {p0, v0}, Lcom/gramforge/NotInterestedTapper;->scanView(Landroid/view/View;I)Z

    move-result p0

    if-eqz p0, :cond_2

    const/4 v0, 0x1

    :cond_2
    return v0
.end method
