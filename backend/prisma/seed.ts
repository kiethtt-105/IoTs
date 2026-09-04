await prisma.user.upsert({
  where: { email: process.env.ADMIN_EMAIL },
  update: {},
  create: {
    email: process.env.ADMIN_EMAIL,
    password: await hash(process.env.ADMIN_PASSWORD),
    role: "ADMIN",
  },
});