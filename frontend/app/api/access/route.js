import { cookies } from "next/headers";

const ACCESS_CODE = process.env.ACCESS_CODE || "6";
const BACKEND_URL = (process.env.BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function verifyWithBackend(code, machineName = "") {
  const response = await fetch(`${BACKEND_URL}/api/public/access/redeem`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      code,
      machine_name: machineName,
    }),
    cache: "no-store",
  });

  const payload = await response.json().catch(() => ({}));
  return { response, payload };
}

function humanizeAccessError(message) {
  const normalized = String(message || "").trim();
  if (normalized === "code_payment_pending") {
    return "这枚访问码还没到账，确认收款后才能兑换登录。";
  }
  if (normalized === "code_not_found") {
    return "访问码不存在。";
  }
  if (normalized === "code_expired") {
    return "访问码已过期。";
  }
  if (normalized === "code_uses_exceeded") {
    return "访问码已达到使用上限。";
  }
  return normalized || "访问码不正确";
}

export async function POST(request) {
  try {
    const body = await request.json();
    const code = String(body?.code || "").trim();
    const machineName = String(body?.machine_name || "").trim();

    if (!code) {
      return Response.json(
        {
          success: false,
          message: "访问码不能为空。",
        },
        { status: 400 },
      );
    }

    let buyerPayload = null;
    let verified = false;

    try {
      const { response, payload } = await verifyWithBackend(code, machineName);
      if (response.ok && payload?.success) {
        verified = true;
        buyerPayload = payload;
      } else if (code === ACCESS_CODE) {
        verified = true;
      } else {
        return Response.json(
          {
            success: false,
            message: humanizeAccessError(payload?.message || payload?.error),
          },
          { status: response.status || 401 },
        );
      }
    } catch (error) {
      if (code === ACCESS_CODE) {
        verified = true;
      } else {
        throw error;
      }
    }

    if (!verified) {
      return Response.json(
        {
          success: false,
          message: "访问码不正确。",
        },
        { status: 401 },
      );
    }

    const cookieStore = await cookies();
    const commonCookie = {
      httpOnly: true,
      sameSite: "lax",
      secure: false,
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    };

    cookieStore.set("jobhelper_access", "granted", commonCookie);
    cookieStore.set("jobhelper_access_code", code.toUpperCase(), commonCookie);

    if (buyerPayload?.buyer_id) {
      cookieStore.set("jobhelper_buyer_id", String(buyerPayload.buyer_id), commonCookie);
    }

    return Response.json({
      success: true,
      message: "验证通过",
      buyer: buyerPayload?.buyer || buyerPayload || null,
    });
  } catch (error) {
    return Response.json(
      {
        success: false,
        message: humanizeAccessError(error?.message),
      },
      { status: 500 },
    );
  }
}

export async function DELETE() {
  const cookieStore = await cookies();
  const expiredCookie = {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: 0,
  };

  cookieStore.set("jobhelper_access", "", expiredCookie);
  cookieStore.set("jobhelper_access_code", "", expiredCookie);
  cookieStore.set("jobhelper_buyer_id", "", expiredCookie);
  cookieStore.set("jobhelper_user_session", "", expiredCookie);
  cookieStore.set("jobhelper_user_id", "", expiredCookie);

  return Response.json({
    success: true,
  });
}
