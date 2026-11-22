package com.gramforge;
import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.ContextWrapper;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewParent;
import android.view.Window;
import android.widget.TextView;
import java.lang.reflect.Method;
import java.util.List;

public final class NotInterestedTapper {
    private static final String TAG = "GramForge";
    private static final String TARGET = "Not interested";
    private NotInterestedTapper() {}

    public static void schedule(final View origin) {
        if (origin == null) return;
        final Handler handler = new Handler(Looper.getMainLooper());
        handler.post(new Runnable() {
            private int tries;
            @Override public void run() {
                try {
                    if (tap(origin)) {
                        Log.i(TAG, "Native Not interested chosen");
                        return;
                    }
                } catch (Exception error) {
                    Log.w(TAG, "Not interested menu lookup failed", error);
                    return;
                }
                if (++tries < 15) handler.postDelayed(this, 140L);
                else Log.w(TAG, "Not interested menu not found");
            }
        });
    }

    private static Activity activityOf(Context context) {
        for (int i=0; i<12 && context!=null; ++i) {
            if (context instanceof Activity) return (Activity)context;
            if (!(context instanceof ContextWrapper)) break;
            Context next = ((ContextWrapper)context).getBaseContext();
            if (next == context) break;
            context = next;
        }
        return null;
    }

    private static Object call(Object object, String name) {
        if (object == null) return null;
        try {
            Method method = object.getClass().getMethod(name);
            return method.invoke(object);
        } catch (ReflectiveOperationException | SecurityException ignored) {
            return null;
        }
    }

    private static boolean tap(View origin) {
        Activity activity = activityOf(origin.getContext());
        if (activity == null) return false;
        Object manager = call(activity, "getSupportFragmentManager");
        if (scanManager(manager, 0)) return true;
        // Some Instagram sheets use an inline overlay in the Activity window.
        Window window = activity.getWindow();
        return window != null && scanView(window.getDecorView(), 0);
    }

    private static boolean scanManager(Object manager, int depth) {
        if (depth > 4) return false;
        Object list = call(manager, "getFragments");
        if (!(list instanceof List)) return false;
        for (Object fragment : (List<?>)list) {
            if (fragment == null) continue;
            Object dialog = call(fragment, "getDialog");
            if (dialog instanceof Dialog) {
                Window window = ((Dialog)dialog).getWindow();
                if (window != null && scanView(window.getDecorView(), 0)) return true;
            }
            Object childManager = call(fragment, "getChildFragmentManager");
            if (childManager != null && scanManager(childManager, depth + 1)) return true;
        }
        return false;
    }

    private static boolean scanView(View view, int depth) {
        if (view == null || depth > 30 || !view.isShown()) return false;
        if (view instanceof TextView) {
            CharSequence text = ((TextView)view).getText();
            if (text != null && TARGET.equalsIgnoreCase(text.toString().trim())) {
                View target = view;
                for (int i=0; i<5 && target!=null; ++i) {
                    if (target.isClickable() && target.isEnabled()) {
                        target.performClick();
                        return true;
                    }
                    ViewParent parent = target.getParent();
                    target = parent instanceof View ? (View)parent : null;
                }
            }
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup)view;
            for (int i=0;i<group.getChildCount();i++) {
                if (scanView(group.getChildAt(i), depth+1)) return true;
            }
        }
        return false;
    }
}
